from mock import patch, MagicMock

from django_webtest import WebTest

from .fake_popit import get_example_popit_json

def fake_api_party_list(*args, **kwargs):
    page = kwargs.get('page')
    return get_example_popit_json(
        'organizations_embed=&page={0}&per_page=2.json'.format(page)
    )

class TestPartyPages(WebTest):

    @patch('candidates.popit.PopIt')
    def test_parties_page(self, mock_popit):
        mock_api = MagicMock()
        mock_api.organizations.get.side_effect = fake_api_party_list
        mock_popit.return_value = mock_api
        response = self.app.get('/parties')
        ul = response.html.find('ul', {'class': 'party-list'})
        lis = ul.find_all('li')
        self.assertEqual(len(lis), 3)
        for i, t in enumerate((
            ('/party/party%3A52/conservative-party', 'Conservative Party'),
            ('/party/party%3A63/green-party', 'Green Party'),
            ('/party/party%3A53/labour-party', 'Labour Party'),
        )):
            expected_url = t[0]
            expected_text = t[1]
            self.assertEqual(lis[i].find('a')['href'], expected_url)
            self.assertEqual(lis[i].find('a').text, expected_text)

