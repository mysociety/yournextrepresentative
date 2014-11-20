import json

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

class TestUpdatePerson(TestCase):

    @patch.object(FakePersonCollection, 'put')
    @patch('candidates.views.requests')
    @patch('candidates.popit.PopIt')
    def test_update_tessa_jowell(self, mock_popit, mock_requests, mocked_put):

        mock_requests.get = fake_get_result

        mock_popit.return_value.organizations = FakeOrganizationCollection
        mock_popit.return_value.persons = FakePersonCollection

        view = MinimalUpdateClass()

        view.create_candidate_list_memberships = MagicMock()
        view.create_party_memberships = MagicMock()

        new_person_data = {
            "date_of_birth": None,
            "email": "foo@example.org",
            "homepage_url": "http://foo.example.org",
            "id": "tessa-jowell",
            "name": "Tessa Jowell",
            "party_memberships": {
                "2010": {
                    "id": "party:53",
                    "name": "Labour Party"
                },
                "2015": {
                    "id": "party:53",
                    "name": "Labour Party"
                }
            },
            "standing_in": {
                "2010": {
                    "mapit_url": "http://mapit.mysociety.org/area/65808",
                    "name": "Dulwich and West Norwood"
                },
                "2015": {
                    "mapit_url": "http://mapit.mysociety.org/area/65808",
                    "name": "Dulwich and West Norwood"
                }
            },
            "twitter_username": "",
            "wikipedia_url": "",
        }

        view.update_person(
            new_person_data,
            {
                'information_source': 'A change made for testing purposes',
                'ip': '127.0.0.1',
                'username': 'tester',
                'version_id': '6054aa38b30b4418',
                'timestamp': '2014-09-28T14:02:44.567413',
            },
            [] # No previous versions, say...
        )
        # FIXME: really we should only need the second call here, but
        # see the FIXME in candidates/update.py:

        self.assertEqual(2, len(mocked_put.call_args_list))

        first_put_call_args = {
                'email': u'foo@example.org',
                'name': u'Tessa Jowell',
                'links': [
                    {
                        'note': 'homepage',
                        'url': 'http://foo.example.org'
                    }
                ],
                'party_memberships': None,
                'standing_in': None,
                'versions': [
                    {
                        'username': 'tester',
                        'ip': '127.0.0.1',
                        'information_source': 'A change made for testing purposes',
                        'version_id': '6054aa38b30b4418',
                        'timestamp': '2014-09-28T14:02:44.567413',
                        'data': new_person_data
                    }],
            }

        second_put_call_args = {
                'email': u'foo@example.org',
                'name': u'Tessa Jowell',
                'links': [
                    {
                        'note': 'homepage',
                        'url': 'http://foo.example.org'
                    }
                ],
                'standing_in': {
                    '2015': {
                        'name': 'Dulwich and West Norwood',
                        'mapit_url': 'http://mapit.mysociety.org/area/65808'
                    },
                    '2010': {
                        'name': 'Dulwich and West Norwood',
                        'mapit_url': 'http://mapit.mysociety.org/area/65808'
                    }
                },
                'versions': [
                    {
                        'username': 'tester',
                        'ip': '127.0.0.1',
                        'information_source': 'A change made for testing purposes',
                        'version_id': '6054aa38b30b4418',
                        'timestamp': '2014-09-28T14:02:44.567413',
                        'data': new_person_data
                    }],
            }


        self.assertTrue(
            equal_call_args(
                [first_put_call_args],
                mocked_put.call_args_list[0][0],
            ),
            "Unexpected first PUT (the one blanking out standing_in and party_memberships",
        )

        self.assertTrue(
            equal_call_args(
                [second_put_call_args],
                mocked_put.call_args_list[1][0],
            ),
            "Unexpected second PUT (the one with real standing_in and party_memberships",
        )

        view.create_candidate_list_memberships.assert_called_once_with(
            'tessa-jowell',
            new_person_data,
        )
        view.create_party_memberships.assert_called_once_with(
            'tessa-jowell',
            new_person_data
        )
