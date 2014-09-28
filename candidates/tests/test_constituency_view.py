from mock import patch

from django_webtest import WebTest

from .fake_popit import FakePersonCollection, FakeOrganizationCollection

class TestConstituencyDetailView(WebTest):

    @patch('candidates.views.PopIt')
    def test_any_constituency_page(self, mock_popit):
        mock_popit.return_value.organizations = FakeOrganizationCollection
        mock_popit.return_value.persons = FakePersonCollection
        # Just a smoke test for the moment:
        response = self.app.get('/constituency/65808/dulwich-and-west-norwood')
        response.mustcontain('Tessa Jowell (Labour Party)')
