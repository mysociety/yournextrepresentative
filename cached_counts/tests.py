from mock import patch, MagicMock
import re

from django.core.management import call_command
from django.test import TestCase

from candidates.tests.test_create_person import mock_create_person
from candidates.tests.fake_popit import get_example_popit_json

from .models import CachedCount

def fake_mp_post_search_results(url, **kwargs):
    mock_requests_response = MagicMock()
    page = "1"
    m = re.search(r'[^_]page=(\d+)', url)
    if m:
        page = m.group(1)
    mock_requests_response.json.return_value = get_example_popit_json(
        'search_mp_posts_page={0}.json'.format(page)
    )
    return mock_requests_response

def create_initial_counts(extra=()):
    initial_counts = (
        {
            'election': '2015',
            'count_type': 'constituency',
            'name': 'Dulwich and West Norwood',
            'count': 10,
            'object_id': '65808'
        },
        {
            'election': '2015',
            'count_type': 'party',
            'name': 'Labour',
            'count': 0,
            'object_id': 'party:53'
        },
        {
            'election': '2015',
            'count_type': 'total',
            'name': 'total',
            'count': 1024,
            'object_id': '2015'
        },
        {
            'election': '2010',
            'count_type': 'total',
            'name': 'total',
            'count': 1500,
            'object_id': '2010'
        },
    )
    initial_counts = initial_counts + extra

    for count in initial_counts:
        CachedCount(**count).save()

class CachedCountTestCase(TestCase):
    def setUp(self):
        create_initial_counts()

    def test_increment_count(self):
        self.assertEqual(CachedCount.objects.get(object_id='party:53').count, 0)
        self.assertEqual(CachedCount.objects.get(object_id='65808').count, 10)
        mock_create_person()
        self.assertEqual(CachedCount.objects.get(object_id='65808').count, 11)
        self.assertEqual(CachedCount.objects.get(object_id='party:53').count, 1)

    def test_reports_top_page(self):
        response = self.client.get('/numbers/')
        self.assertEqual(response.status_code, 200)


class TestCachedCountsCreateCommand(TestCase):

    @patch('candidates.popit.requests')
    def test_cached_counts_create_command(self, mock_requests):
        mock_requests.get.side_effect = fake_mp_post_search_results
        call_command('cached_counts_create')
        non_zero_counts = CachedCount.objects.exclude(count=0). \
            order_by('count_type', 'name', 'object_id'). \
            values_list()
        non_zero_counts = list(non_zero_counts)
        expected_counts = [
            (514, u'constituency', u'Dulwich and West Norwood', 8, u'65808'),
            (217, u'party', u"All People's Party", 1, u'party:2137'),
            (288, u'party', u'Conservative Party', 1, u'party:52'),
            (230, u'party', u'Green Party', 1, u'party:63'),
            (390, u'party', u'Independent', 1, u'ynmp-party:2'),
            (287, u'party', u'Labour Party', 1, u'party:53'),
            (84, u'party', u'Liberal Democrats', 1, u'party:90'),
            (179, u'party', u'Trade Unionist and Socialist Coalition', 1, u'party:804'),
            (145, u'party', u'UK Independence Party (UKIP)', 1, u'party:85'),
            (1155, u'total', u'new_candidates', 6, u'new_candidates'),
            (1160, u'total', u'standing_again', 2, u'standing_again'),
            (1159, u'total', u'standing_again_different_party', 2, u'standing_again_different_party'),
            (1156, u'total', u'total_2010', 2, u'candidates_2010'),
            (1157, u'total', u'total_2015', 8, u'candidates_2015'),
        ]
