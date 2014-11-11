from django.test import TestCase

from mock import patch, MagicMock

from .fake_popit import (
    fake_get_result,
    FakePersonCollection, FakeOrganizationCollection
)
from .helpers import equal_call_args
from ..views import PersonUpdateMixin, CandidacyMixin, PopItApiMixin

class MinimalUpdateClass(PersonUpdateMixin, CandidacyMixin, PopItApiMixin):
    pass

class TestCreatePerson(TestCase):

    @patch.object(FakePersonCollection, 'post')
    @patch('candidates.views.requests')
    @patch('candidates.models.PopIt')
    def test_create_jane_doe(self, mock_popit, mock_requests, mocked_post):

        mocked_post.return_value = {
            'result': {
                'id': 'jane-doe'
            }
        }

        mock_requests.get = fake_get_result

        mock_popit.return_value.organizations = FakeOrganizationCollection
        mock_popit.return_value.persons = FakePersonCollection

        view = MinimalUpdateClass()

        view.create_candidate_list_memberships = MagicMock()
        view.create_party_memberships = MagicMock()

        new_person_data = {
            "date_of_birth": None,
            "email": "jane@example.org",
            "homepage_url": "http://janedoe.example.org",
            "name": "Jane Doe",
            "party_memberships": {
                "2015": {
                    "id": "party:53",
                    "name": "Labour Party"
                }
            },
            "standing_in": {
                "2015": {
                    "mapit_url": "http://mapit.mysociety.org/area/65808",
                    "name": "Dulwich and West Norwood"
                }
            },
            "twitter_username": "",
            "wikipedia_url": "",
        }

        view.create_person(
            new_person_data,
            {
                'information_source': 'A change made for testing purposes',
                'ip': '127.0.0.1',
                'username': 'tester',
                'version_id': '6054aa38b30b4418',
                'timestamp': '2014-09-28T14:02:44.567413',
            },
        )

        expected_args = {
            'email': u'jane@example.org',
            'id': '1',
            'links': [
                {
                    'note': 'homepage',
                    'url': 'http://janedoe.example.org'
                }
            ],
            'name': u'Jane Doe',
            'standing_in': {
                '2015': {
                    'name': 'Dulwich and West Norwood',
                    'mapit_url': 'http://mapit.mysociety.org/area/65808'}
            },
            'versions': [
                {
                    'information_source': 'A change made for testing purposes',
                    'username': 'tester',
                    'ip': '127.0.0.1',
                    'version_id': '6054aa38b30b4418',
                    'timestamp': '2014-09-28T14:02:44.567413',
                    'data': {
                        'twitter_username': '',
                        'standing_in': {
                            '2015': {
                                'name': 'Dulwich and West Norwood',
                                'mapit_url': 'http://mapit.mysociety.org/area/65808'
                            }
                        },
                        'homepage_url': 'http://janedoe.example.org',
                        'date_of_birth': None,
                        'name': 'Jane Doe',
                        'wikipedia_url': '',
                        'party_memberships': {
                            '2015': {
                                'id': 'party:53',
                                'name': 'Labour Party'
                            }
                        },
                        'email': 'jane@example.org',
                        'id': '1'
                    }
                }
            ],
        }

        # Then we expect one post, with the right data:
        self.assertEqual(1, len(mocked_post.call_args_list))
        self.assertTrue(
            equal_call_args(
                [expected_args],
                mocked_post.call_args[0]
            ),
            "update_person was called with unexpected values"
        )

        view.create_candidate_list_memberships.assert_called_once_with(
            'jane-doe',
            new_person_data,
        )
        view.create_party_memberships.assert_called_once_with(
            'jane-doe',
            new_person_data
        )
