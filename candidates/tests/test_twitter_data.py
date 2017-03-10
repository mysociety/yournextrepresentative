from __future__ import print_function, unicode_literals

from mock import Mock, PropertyMock,call, patch

from django.test import TestCase, override_settings

from candidates.management.twitter import TwitterAPIData

from .factories import PersonExtraFactory


def fake_twitter_api_post(*args, **kwargs):
    data = kwargs['data']
    mock_result = Mock()
    if 'screen_name' in data:
        if data['screen_name'] == 'mhl20,struan':
            mock_result.json.return_value = [
                {'id': 1234, 'screen_name': 'mhl20'},
                {'id': 5678, 'screen_name': 'struan'},
            ]
            return mock_result
        elif data['screen_name'] == 'symroe':
            mock_result.json.return_value = [
                {'id': 9012, 'screen_name': 'symroe'}
            ]
            return mock_result
        elif data['screen_name'] == 'onlynonexistent':
            mock_result.json.return_value = {
                "errors": [
                    {
                        "code": 17,
                        "message": "No user matches for specified terms."
                    }
                ]
            }
            return mock_result
    elif 'user_id' in data:
        if data['user_id'] == '42':
            mock_result.json.return_value = [
                {'id': 42, 'screen_name': 'FooBarBazQuux'}
            ]
            return mock_result
        if data['user_id'] == '13984716923847632':
            mock_result.json.return_value = {
                "errors": [
                    {
                        "code": 17,
                        "message": "No user matches for specified terms."
                    }
                ]
            }
            return mock_result
    raise Exception("No Twitter API stub for {0} {1}".format(args, kwargs))


class TestTwitterData(TestCase):

    def test_error_on_missing_token(self):
        with self.assertRaisesRegexp(
                Exception,
                r'TWITTER_APP_ONLY_BEARER_TOKEN was not set'):
            TwitterAPIData()

    @override_settings(TWITTER_APP_ONLY_BEARER_TOKEN='madeuptoken')
    @patch('candidates.management.twitter.requests')
    def test_makes_requests(self, mock_requests):
        TwitterAPIData.MAX_IN_A_REQUEST = 2
        twitter_data = TwitterAPIData()
        mock_requests.post.side_effect = fake_twitter_api_post
        twitter_results = list(twitter_data.twitter_results(
            'screen_name',
            ['mhl20', 'struan', 'symroe']))
        self.assertEqual(
            mock_requests.post.mock_calls,
            [
                call(
                    'https://api.twitter.com/1.1/users/lookup.json',
                    headers={u'Authorization': u'Bearer madeuptoken'},
                    data={u'screen_name': u'mhl20,struan'}),
                call(
                    'https://api.twitter.com/1.1/users/lookup.json',
                    headers={u'Authorization': u'Bearer madeuptoken'},
                    data={u'screen_name': u'symroe'}),
            ]
        )
        self.assertEqual(
            twitter_results,
            [
                {'id': 1234, 'screen_name': 'mhl20'},
                {'id': 5678, 'screen_name': 'struan'},
                {'id': 9012, 'screen_name': 'symroe'},
            ]
        )

    @override_settings(TWITTER_APP_ONLY_BEARER_TOKEN='madeuptoken')
    @patch('candidates.management.twitter.requests')
    def test_zero_results_for_screen_name_lookup(self, mock_requests):
        twitter_data = TwitterAPIData()
        mock_requests.post.side_effect = fake_twitter_api_post
        twitter_results = list(twitter_data.twitter_results(
            'screen_name',
            ['onlynonexistent']))
        self.assertEqual(twitter_results, [])

    @override_settings(TWITTER_APP_ONLY_BEARER_TOKEN='madeuptoken')
    @patch('candidates.management.twitter.requests')
    def test_zero_results_for_user_id_lookup(self, mock_requests):
        twitter_data = TwitterAPIData()
        mock_requests.post.side_effect = fake_twitter_api_post
        twitter_results = list(twitter_data.twitter_results(
            'user_id',
            ['13984716923847632']))
        self.assertEqual(twitter_results, [])

    @override_settings(TWITTER_APP_ONLY_BEARER_TOKEN='madeuptoken')
    def test_all_screen_names(self):
        joe = PersonExtraFactory.create(
            base__id='1',
            base__name='Joe Bloggs').base
        joe.contact_details.create(
            value='joenotreallyatwitteraccount',
            contact_type='twitter',
        )
        jane = PersonExtraFactory.create(
            base__id='2',
            base__name='Jane Bloggs').base
        jane.contact_details.create(
            value='janenotreallyatwitteraccount',
            contact_type='twitter')
        twitter_data = TwitterAPIData()
        self.assertEqual(
            ['janenotreallyatwitteraccount', 'joenotreallyatwitteraccount'],
            sorted(twitter_data.all_screen_names)
        )

    @override_settings(TWITTER_APP_ONLY_BEARER_TOKEN='madeuptoken')
    def tests_all_user_ids(self):
        joe = PersonExtraFactory.create(
            base__id='1',
            base__name='Joe Bloggs').base
        joe.identifiers.create(
            identifier='246',
            scheme='twitter',
        )
        jane = PersonExtraFactory.create(
            base__id='2',
            base__name='Jane Bloggs').base
        jane.identifiers.create(
            identifier='357',
            scheme='twitter')
        twitter_data = TwitterAPIData()
        self.assertEqual(
            ['246', '357'],
            sorted(twitter_data.all_user_ids)
        )

    @override_settings(TWITTER_APP_ONLY_BEARER_TOKEN='madeuptoken')
    def test_update_individual_data(self):
        twitter_data = TwitterAPIData()
        twitter_data.update_id_mapping(
            {
                'id': 42,
                'screen_name': 'FooBarBazQuux',
                'profile_image_url_https': 'https://example.com/foo.jpg',
            }
        )
        self.assertEqual(
            twitter_data.screen_name_to_user_id,
            {'foobarbazquux': '42'})
        self.assertEqual(
            twitter_data.user_id_to_screen_name,
            {'42': 'FooBarBazQuux'})
        self.assertEqual(
            twitter_data.user_id_to_photo_url,
            {'42': 'https://example.com/foo.jpg'})

    @override_settings(TWITTER_APP_ONLY_BEARER_TOKEN='madeuptoken')
    @patch('candidates.management.twitter.requests')
    @patch('candidates.management.twitter.TwitterAPIData.update_id_mapping')
    @patch('candidates.management.twitter.TwitterAPIData.all_user_ids', new_callable=PropertyMock)
    @patch('candidates.management.twitter.TwitterAPIData.all_screen_names', new_callable=PropertyMock)
    def test_update_from_api(
            self,
            mock_all_screen_names,
            mock_all_user_ids,
            mock_update_id_mapping,
            mock_requests):
        mock_requests.post.side_effect = fake_twitter_api_post
        twitter_data = TwitterAPIData()
        mock_all_user_ids.return_value = ['1234', '42']
        mock_all_screen_names.return_value = ['mhl20', 'struan', 'symroe']
        twitter_data.user_id_to_screen_name = {
            '1234': 'mhl20',
        }
        twitter_data.update_from_api()
        self.assertEqual(
            mock_update_id_mapping.mock_calls,
            [
                call({'id': 1234, 'screen_name': 'mhl20'}),
                call({'id': 5678, 'screen_name': 'struan'}),
                call({'id': 9012, 'screen_name': 'symroe'}),
                call({'id': 42, 'screen_name': 'FooBarBazQuux'}),
            ]
        )

    @override_settings(TWITTER_APP_ONLY_BEARER_TOKEN='madeuptoken')
    @patch('candidates.management.twitter.requests')
    def test_unfaked_urls_raise_exception(self, mock_requests):
        TwitterAPIData.MAX_IN_A_REQUEST = 2
        twitter_data = TwitterAPIData()
        mock_requests.post.side_effect = fake_twitter_api_post
        with self.assertRaises(Exception):
            list(twitter_data.twitter_results(
                'screen_name',
                ['foo', 'bar']))
