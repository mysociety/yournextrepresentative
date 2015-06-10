from mock import patch

from django_webtest import WebTest

from .auth import TestUserMixin
from .fake_popit import (FakePersonCollection, FakeOrganizationCollection,
                         FakePostCollection)

@patch('candidates.popit.PopIt')
class TestConstituencyDetailView(TestUserMixin, WebTest):

    def test_any_constituency_page_without_login(self, mock_popit):
        mock_popit.return_value.organizations = FakeOrganizationCollection
        mock_popit.return_value.persons = FakePersonCollection
        mock_popit.return_value.posts = FakePostCollection

        # Just a smoke test for the moment:
        response = self.app.get('/posts')
        self.assertEqual(response.status_code, 200)
