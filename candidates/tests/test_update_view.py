# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json

from django.utils.six.moves.urllib_parse import urlsplit

from django_webtest import WebTest
from webtest.forms import Text

from .auth import TestUserMixin

from popolo.models import Person, Membership

from candidates.models import ExtraField
from .factories import CandidacyExtraFactory, PersonExtraFactory
from .uk_examples import UK2015ExamplesMixin


def membership_id_set(person):
    return set(person.memberships.values_list('pk', flat=True))


class TestUpdatePersonView(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestUpdatePersonView, self).setUp()
        person_extra = PersonExtraFactory.create(
            base__id='2009',
            base__name='Tessa Jowell'
        )

        CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.green_party_extra.base
        )

    def test_update_person_should_not_lose_existing_not_standing(self):
        # Pretend that we know she wasn't standing in the earlier election:
        tessa = Person.objects.get(pk=2009)
        tessa.extra.not_standing.add(self.earlier_election)
        response = self.app.get('/person/2009/update', user=self.user)
        form = response.forms['person-details']
        form.submit()
        self.assertEqual(
            list(tessa.extra.not_standing.all()),
            [self.earlier_election])

    def test_update_person_view_get_without_login(self):
        response = self.app.get('/person/2009/update')
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual('/accounts/login/', split_location.path)
        self.assertEqual('next=/person/2009/update', split_location.query)

    def test_update_person_view_get_refused_copyright(self):
        response = self.app.get('/person/2009/update', user=self.user_refused)
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual('/copyright-question', split_location.path)
        self.assertEqual('next=/person/2009/update', split_location.query)

    def test_update_person_view_get(self):
        # For the moment just check that the form's actually there:
        response = self.app.get('/person/2009/update', user=self.user)
        form = response.forms['person-details']
        self.assertIsNotNone(form)

    def test_update_person_submission_copyright_refused(self):
        response = self.app.get('/person/2009/update', user=self.user)
        form = response.forms['person-details']
        form['wikipedia_url'] = 'http://en.wikipedia.org/wiki/Tessa_Jowell'
        form['party_gb_2015'] = self.labour_party_extra.base_id
        form['source'] = "Some source of this information"
        submission_response = form.submit(user=self.user_refused)
        split_location = urlsplit(submission_response.location)
        self.assertEqual('/copyright-question', split_location.path)
        self.assertEqual('next=/person/2009/update', split_location.query)

    def test_update_person_submission(self):
        memberships_before = membership_id_set(Person.objects.get(pk=2009))
        response = self.app.get(
            '/person/2009/update',
            user=self.user_who_can_lock,
        )
        form = response.forms['person-details']
        form['wikipedia_url'] = 'http://en.wikipedia.org/wiki/Tessa_Jowell'
        form['party_gb_2015'] = self.labour_party_extra.base_id
        form['source'] = "Some source of this information"
        submission_response = form.submit()

        person = Person.objects.get(id='2009')
        party = person.memberships.filter(role='Candidate')

        self.assertEqual(party.count(), 1)
        self.assertEqual(party[0].on_behalf_of.extra.slug, 'party:53')

        links = person.links.all()
        self.assertEqual(links.count(), 1)
        self.assertEqual(links[0].url, 'http://en.wikipedia.org/wiki/Tessa_Jowell')

        # It should redirect back to the same person's page:
        split_location = urlsplit(submission_response.location)
        self.assertEqual(
            '/person/2009',
            split_location.path
        )
        self.assertEqual(
            memberships_before,
            membership_id_set(person))

    def test_update_dd_mm_yyyy_birth_date(self):
        memberships_before = membership_id_set(Person.objects.get(pk=2009))
        response = self.app.get(
            '/person/2009/update',
            user=self.user_who_can_lock,
        )
        form = response.forms['person-details']
        form['birth_date'] = '1/4/1875'
        form['source'] = "An update for testing purposes"
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual('/person/2009', split_location.path)

        person = Person.objects.get(id='2009')
        self.assertEqual(person.birth_date, '1875-04-01')
        self.assertEqual(
            memberships_before,
            membership_id_set(person))

    def test_update_person_extra_fields(self):
        memberships_before = membership_id_set(Person.objects.get(pk=2009))
        ExtraField.objects.create(
            type='url',
            key='cv',
            label='CV or Resumé',
        )
        ExtraField.objects.create(
            type='longer-text',
            key='notes',
            label='Notes',
        )
        response = self.app.get(
            '/person/2009/update',
            user=self.user_who_can_lock,
        )
        form = response.forms['person-details']
        form['birth_date'] = '1/4/1875'
        form['source'] = "An update for testing purposes"
        form['cv'] = 'http://example.org/cv.pdf'
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual('/person/2009', split_location.path)

        person = Person.objects.get(id='2009')
        self.assertEqual(person.birth_date, '1875-04-01')
        versions_data = json.loads(person.extra.versions)
        self.assertEqual(
            versions_data[0]['data']['extra_fields'],
            {
                'cv': 'http://example.org/cv.pdf',
                'notes': '',
            }
        )
        self.assertEqual(
            memberships_before,
            membership_id_set(person))

    def test_update_person_add_new_candidacy(self):
        memberships_before = membership_id_set(Person.objects.get(pk=2009))
        response = self.app.get('/person/2009/update', user=self.user)
        # Now fake the addition of elements to the form as would
        # happen with the Javascript addition of a new candidacy.
        form = response.forms['person-details']
        for name, value in [
                ('extra_election_id', 'local.maidstone.2016-05-05'),
                ('party_gb_local.maidstone.2016-05-05', self.labour_party_extra.base.id),
                ('constituency_local.maidstone.2016-05-05', 'DIW:E05005004'),
                ('standing_local.maidstone.2016-05-05', 'standing'),
                ('source', 'Testing dynamic election addition'),
        ]:
            field = Text(form, 'input', None, None, value)
            form.fields[name] = [field]
            form.field_order.append((name, field))
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual('/person/2009', split_location.path)

        person = Person.objects.get(pk=2009)
        memberships_afterwards = membership_id_set(person)
        extra_membership_ids = memberships_afterwards - memberships_before
        self.assertEqual(len(extra_membership_ids), 1)
        new_candidacy = Membership.objects.get(pk=list(extra_membership_ids)[0])
        self.assertEqual(
            new_candidacy.post.label, 'Shepway South Ward')
        self.assertEqual(
            new_candidacy.extra.election.slug, 'local.maidstone.2016-05-05')
        self.assertEqual(
            new_candidacy.on_behalf_of.name, 'Labour Party')
        same_before_and_after = memberships_before & memberships_afterwards
        self.assertEqual(len(same_before_and_after), 1)
