from django.test import TestCase

from candidates.models import LoggedAction

from .auth import TestUserMixin
from . import factories

class TestLoggedAction(TestUserMixin, TestCase):

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
