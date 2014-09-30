from mock import patch, Mock

from django_webtest import WebTest

@patch('candidates.views.PopIt')
@patch('candidates.views.requests')
class TestAutocompletePartyView(WebTest):

    def test_autocomplete(self, mock_requests, mock_popit):
        fake_search_result = {
            "total": 9,
            "page": 1,
            "per_page": 30,
            "has_more": False,
            "result": [
                {"name": "Socialist Labour Party"},
                {"name": "Labour Party"},
                {"name": "Democratic Labour Party"},
                {"name": "Labour and Co-operative"},
                {"name": "The Labour Party"},
                {"name": "Labour Party of Northern Ireland"},
                {"name": "SDLP (Social Democratic & Labour Party)"},
                {"name": "The Individuals Labour and Tory (TILT)"},
                {"name": "Liverpool Labour Community Party"},
            ],
        }
        mock_requests.get.return_value = Mock(**{
            'json.return_value': fake_search_result
        })
        response = self.app.get('/autocomplete/party?term=lab')
        self.assertEqual(
            response.json,
            [
                "lab",
                "Labour Party",
                "Socialist Labour Party",
                "SDLP (Social Democratic & Labour Party)",
                "Democratic Labour Party",
                "The Labour Party",
                "Labour and Co-operative",
                "Labour Party of Northern Ireland",
                "The Individuals Labour and Tory (TILT)",
                "Liverpool Labour Community Party"
            ]
        )
