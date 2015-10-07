from mock import patch,  MagicMock
from datetime import date

import re

from django_webtest import WebTest

from elections.models import Election

from .fake_popit import get_example_popit_json, FakePostCollection

def fake_election_search_results(url, **kwargs):
    mock_requests_response = MagicMock()
    page = "1"
    m = re.search(r'[^_]page=(\d+)', url)
    if m:
        page = m.group(1)
    mock_requests_response.json.return_value = get_example_popit_json(
        'generic_posts_embed={0}.json'.format(page)
    )
    return mock_requests_response


def fake_post_search_results(url, **kwargs):
    mock_requests_response = MagicMock()
    mock_requests_response.json.return_value = get_example_popit_json(
        'generic_posts_embed=.json'
    )
    return mock_requests_response


@patch('candidates.popit.PopIt')
class TestPostsView(WebTest):

    @patch('candidates.popit.requests')
    def test_single_election_posts_page(self, mock_requests, mock_popit):
        mock_requests.get.side_effect = fake_post_search_results
        mock_popit.return_value.posts = FakePostCollection

        response = self.app.get('/posts')

        self.assertTrue(
            response.html.find(
                'h2', text='2015 General Election'
            )
        )

        self.assertTrue(
            response.html.find(
                'a', text='Member of Parliament for Camberwell and Peckham'
            )
        )


    @patch('candidates.popit.requests')
    @patch('candidates.views.posts.Election.objects.current')
    def test_two_elections_posts_page(self, mock_current, mock_requests, mock_popit):
        mock_requests.get.side_effect = fake_post_search_results
        mock_popit.return_value.posts = FakePostCollection
        mock_current.return_value = Election.objects.all()

        response = self.app.get('/posts')

        self.assertTrue(
            response.html.find(
                'h2', text='2010 General Election'
            )
        )

        self.assertTrue(
            response.html.find(
                'h2', text='2015 General Election'
            )
        )
