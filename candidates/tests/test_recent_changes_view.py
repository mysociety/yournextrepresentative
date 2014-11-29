from django_webtest import WebTest

from .auth import TestUserMixin
from ..models import LoggedAction

class TestRecentChangesView(TestUserMixin, WebTest):

    def setUp(self):
        self.action1 = LoggedAction.objects.create(
            user=self.user,
            action_type='person-create',
            ip_address='127.0.0.1',
            popit_person_id='9876',
            popit_person_new_version='1234567890abcdef',
            source='Just for tests...',
        )
        self.action2 = LoggedAction.objects.create(
            user=self.user,
            action_type='candidacy-delete',
            ip_address='127.0.0.1',
            popit_person_id='1234',
            popit_person_new_version='987654321',
            source='Also just for testing',
        )

    def tearDown(self):
        self.action2.delete()
        self.action1.delete()

    def test_recent_changes_page(self):
        # Just a smoke test to check that the page loads:
        response = self.app.get('/recent-changes')
        table = response.html.find('table')
        self.assertEqual(3, len(table.find_all('tr')))
