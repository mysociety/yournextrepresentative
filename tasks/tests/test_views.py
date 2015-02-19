from mock import patch, MagicMock

from django.test import TestCase

from cached_counts.tests import create_initial_counts
from candidates.tests.fake_popit import get_example_popit_json


def fake_field_search_results(url, **kwargs):
    mock_requests_response = MagicMock()
    page = "1"
    mock_requests_response.json.return_value = get_example_popit_json(
        'search_incomplete_email_page={0}.json'.format(page),
    )
    return mock_requests_response


class TestFieldView(TestCase):
    def setUp(self):
        extra = (
            {
                'count_type': 'total',
                'name': 'candidates_2015',
                'count': 3000,
                'object_id': 'candidates_2015',
            },
        )
        create_initial_counts(extra)

    @patch('candidates.popit.PopIt')
    @patch('tasks.views.requests')
    def test_context_data(self, mock_requests, mock_popit):
        url = '/tasks/email/'
        mock_requests.get.side_effect = fake_field_search_results

        response = self.client.get(url)
        self.assertEqual(response.context['field'], 'email')
        self.assertEqual(response.context['candidates_2015'], 3000)
        self.assertEqual(response.context['next'], 2)
        self.assertFalse('prev' in response.context)
        self.assertEqual(response.context['results_count'], 1145)

    @patch('candidates.popit.PopIt')
    @patch('tasks.views.requests')
    def test_template_used(self, mock_requests, mock_popit):
        mock_requests.get.side_effect = fake_field_search_results
        response = self.client.get('/tasks/email/')
        self.assertTemplateUsed(response, 'tasks/field.html')
