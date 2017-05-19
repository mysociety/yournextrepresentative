from django.test import TestCase

from candidates.models import LoggedAction, PostExtraElection

from .auth import TestUserMixin
from .uk_examples import UK2015ExamplesMixin
from . import factories

class TestLoggedAction(TestUserMixin, UK2015ExamplesMixin, TestCase):

    def test_logged_action_repr(self):
        person = factories.PersonExtraFactory.create(
            base__id='9876',
            base__name='Test Candidate',
        ).base
        action = LoggedAction.objects.create(
            user=self.user,
            action_type='person-create',
            ip_address='127.0.0.1',
            person=person,
            popit_person_new_version='1234567890abcdef',
            source='Just for tests...',
        )
        self.assertEqual(
            repr(action),
            str("<LoggedAction username='john' action_type='person-create'>"),
        )

    def test_subject_person(self):
        person = factories.PersonExtraFactory.create(
            base__id='9876',
            base__name='Test Candidate',
        ).base
        action = LoggedAction.objects.create(
            user=self.user,
            action_type='person-create',
            ip_address='127.0.0.1',
            person=person,
            popit_person_new_version='1234567890abcdef',
            source='Just for tests...',
        )
        self.assertEqual(
            action.subject_html,
            '<a href="/person/9876">Test Candidate (9876)</a>',
        )

    def test_subject_post(self):
        action = LoggedAction.objects.create(
            user=self.user,
            action_type='constituency-lock',
            ip_address='127.0.0.1',
            post=self.camberwell_post_extra.base,
            popit_person_new_version='1234567890abcdef',
            source='Just for tests...',
        )
        self.assertEqual(
            action.subject_html,
            '<a href="/election/2015/post/65913/camberwell-and-peckham">Camberwell and Peckham (65913)</a>',
        )

    def test_guess_of_postextraelection_current(self):
        action = LoggedAction.objects.create(
            user=self.user,
            action_type='constituency-lock',
            ip_address='127.0.0.1',
            post=self.camberwell_post_extra.base,
            popit_person_new_version='1234567890abcdef',
            source='Just for tests...',
        )
        self.assertEqual(
            action.post_election_guess,
            PostExtraElection.objects.get(
                election=self.election,
                postextra=self.camberwell_post_extra)
        )

    def test_guess_of_postextraelection_past(self):
        ced_area_type = factories.AreaTypeFactory.create(name='CED')
        past_election = factories.ElectionFactory.create(
            current=False,
            name='2017 Essex County Council local election',
            election_date='2017-05-04',
            area_types=(ced_area_type,),
        )
        council = factories.OrganizationFactory.create(
            name='Essex County Council')
        post = factories.PostExtraFactory.create(
            elections=(past_election,),
            slug='CED:19782',
            base__label='CED:19782',
            party_set=self.gb_parties,
            base__organization=council,
        ).base
        action = LoggedAction.objects.create(
            user=self.user,
            action_type='constituency-lock',
            ip_address='127.0.0.1',
            post=post,
            popit_person_new_version='1234567890abcdef',
            source='Just for tests...',
        )
        self.assertEqual(
            action.post_election_guess,
            PostExtraElection.objects.get(
                election=past_election,
                postextra=post.extra)
        )
