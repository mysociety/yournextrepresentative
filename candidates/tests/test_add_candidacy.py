from __future__ import unicode_literals


from django.core.urlresolvers import reverse
from django.utils.six import text_type
from django.utils.six.moves.urllib_parse import urlsplit

from django_webtest import WebTest
from popolo.models import Membership

from candidates.models import PostExtra, LoggedAction

from .auth import TestUserMixin
from .settings import SettingsMixin
from .uk_examples import UK2015ExamplesMixin
from . import factories


class TestAddCandidacyWizard(TestUserMixin, SettingsMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestAddCandidacyWizard, self).setUp()
        self.person_extra = factories.PersonExtraFactory.create(
            base__id=1234,
            base__name='Testy McTestface',
            base__gender='neuter',
            base__email='mctestface@example.com',
        )
        self.person = self.person_extra.base
        self.wizard_url = reverse(
            'person-update-add-candidacy',
            kwargs={'person_id': self.person.id})

    def test_only_logged_in_users(self):
        response = self.app.get(self.wizard_url)
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual(
            split_location.path, '/accounts/login/')
        self.assertEqual(
            split_location.query, 'next=/person/1234/update/add-candidacy')

    def test_no_posts_for_election(self):
        factories.ElectionFactory.create(
            slug='2058',
            name='2058 Galactic Senate Election',
            for_post_role='Senator',
        )
        response = self.app.get(self.wizard_url, user=self.user)
        election_form = response.forms['add-candidacy-wizard']
        election_form['election-election'].select(
            text='2058 Galactic Senate Election')
        submission_response = election_form.submit()
        # There should be an error since there are no posts for this
        # election:
        form_after_submission = \
            submission_response.forms['add-candidacy-wizard']
        self.assertTrue(form_after_submission['election-election'])
        self.assertIn(
            'No posts have been created for the 2058 Galactic Senate Election',
            submission_response)

    def test_all_posts_for_election_locked(self):
        PostExtra.objects.update(candidates_locked=True)
        response = self.app.get(self.wizard_url, user=self.user)
        election_form = response.forms['add-candidacy-wizard']
        election_form['election-election'].select(text='2015 General Election')
        submission_response = election_form.submit()
        # We should still be on the election-picking page, and have a
        # validation error saying that no posts for that election were
        # unlocked.
        form_after_submission = \
            submission_response.forms['add-candidacy-wizard']
        self.assertTrue(form_after_submission['election-election'])
        expected_error = 'There are no unlocked posts in the election ' \
            '2015 General Election - if you think the candidates for this ' \
            'election are wrong or incomplete, please ' \
            '<a href="mailto:yournextmp-support@example.org">' \
            'contact us</a>.'
        self.assertIn(expected_error, submission_response)

    def test_election_with_single_post(self):
        election = factories.ElectionFactory.create(
            slug='2058',
            name='2058 Galactic Senate Election',
            for_post_role='Senator',
        )
        party_set = factories.PartySetFactory.create(
            slug='pg', name='Pan-Galactic Party Set'
        )
        area_extra = factories.AreaExtraFactory.create(
            base__identifier='area:tatooine',
            base__name='Tatooine',
            type=factories.AreaTypeFactory.create(),
        )
        factories.PostExtraFactory.create(
            elections=(election,),
            base__organization=self.commons,
            base__area=area_extra.base,
            slug='tatooine',
            base__label='Senator for Tatooine',
            party_set=party_set,
        )
        party = factories.PartyExtraFactory(
            slug='tip',
            base__name='Tatooine Independence Party',
        )
        party_set.parties.add(party.base)
        # Now step through the election selection page - it should go
        # directly to party select afterwards:
        response = self.app.get(self.wizard_url, user=self.user)
        election_form = response.forms['add-candidacy-wizard']
        election_form['election-election'].select(
            text='2058 Galactic Senate Election')
        submission_response = election_form.submit()
        # There should be an error since there are no posts for this
        # election:
        form_after_submission = \
            submission_response.forms['add-candidacy-wizard']
        party_select = form_after_submission['party-party']
        self.assertEqual(
            [('party:none', False, ''),
             (str(party.base.id), False, 'Tatooine Independence Party')],
            party_select.options
        )

    def test_all_steps_successful(self):
        # Select the election:
        response = self.app.get(self.wizard_url, user=self.user)
        election_form = response.forms['add-candidacy-wizard']
        election_form['election-election'].select(
            text='2015 General Election')
        response = election_form.submit()
        # Select the post:
        post_form = response.forms['add-candidacy-wizard']
        post_form['post-post'].select(text='Dulwich and West Norwood')
        response = post_form.submit()
        # Select the party:
        party_form = response.forms['add-candidacy-wizard']
        party_form['party-party'].select(text='Labour Party')
        response = party_form.submit()
        # Explain the source:
        source_form = response.forms['add-candidacy-wizard']
        source_form['source-source'] = 'Testing adding a candidacy'
        response = source_form.submit()
        # Now check we're redirected back to the person edit page:
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual(
            split_location.path,
            '/person/1234/update'
        )
        # And check that all the changes we expect have been made.
        # The action must have been logged:
        la = LoggedAction.objects.order_by('updated').last()
        self.assertEqual(la.user, self.user)
        self.assertEqual(la.note, None)
        self.assertTrue(la.popit_person_new_version)
        self.assertEqual(la.person, self.person)
        self.assertEqual(la.source, 'Testing adding a candidacy')
        # Now check that that person has a new candidacy:
        m = Membership.objects.select_related('extra', 'on_behalf_of').get(
            person=self.person,
            role='Candidate')
        self.assertEqual(m.on_behalf_of.name, 'Labour Party')
        self.assertEqual(m.post, self.dulwich_post_extra.base)

    def test_locked_at_last_minute(self):
        # Select the election:
        response = self.app.get(self.wizard_url, user=self.user)
        election_form = response.forms['add-candidacy-wizard']
        election_form['election-election'].select(
            text='2015 General Election')
        response = election_form.submit()
        # Select the post:
        post_form = response.forms['add-candidacy-wizard']
        post_form['post-post'].select(text='Dulwich and West Norwood')
        response = post_form.submit()
        # Select the party:
        party_form = response.forms['add-candidacy-wizard']
        party_form['party-party'].select(text='Labour Party')
        response = party_form.submit()
        # Now lock that post:
        self.dulwich_post_extra.candidates_locked = True
        self.dulwich_post_extra.save()
        # Set a source and try to submit:
        source_form = response.forms['add-candidacy-wizard']
        source_form['source-source'] = 'Testing adding a candidacy'
        with self.assertRaises(Exception) as context:
            response = source_form.submit()
        self.assertEqual(
            text_type(context.exception),
            'Attempt to edit a candidacy in a locked constituency')

    def test_all_steps_with_party_list_position_successful(self):
        self.election.party_lists_in_use = True
        self.election.save()
        # Now go through all the steps, but set a party list position
        # too:
        # Select the election:
        response = self.app.get(self.wizard_url, user=self.user)
        election_form = response.forms['add-candidacy-wizard']
        election_form['election-election'].select(
            text='2015 General Election')
        response = election_form.submit()
        # Select the post:
        post_form = response.forms['add-candidacy-wizard']
        post_form['post-post'].select(text='Dulwich and West Norwood')
        response = post_form.submit()
        # Select the party:
        party_form = response.forms['add-candidacy-wizard']
        party_form['party-party'].select(text='Labour Party')
        party_form['party-party_list_position'] = 3
        response = party_form.submit()
        # Explain the source:
        source_form = response.forms['add-candidacy-wizard']
        source_form['source-source'] = 'Testing adding a candidacy'
        response = source_form.submit()
        # Now check we're redirected back to the person edit page:
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual(
            split_location.path,
            '/person/1234/update'
        )
        # Now check that that person has a new candidacy:
        m = Membership.objects.select_related('extra', 'on_behalf_of').get(
            person=self.person,
            role='Candidate')
        self.assertEqual(m.extra.party_list_position, 3)
