import json

from django.test import TestCase

from mock import patch, MagicMock

from .fake_popit import (
    FakePersonCollection, FakeOrganizationCollection
)
from .helpers import equal_call_args
from ..views import PersonUpdateMixin, CandidacyMixin, PopItApiMixin

class MinimalUpdateClass(PersonUpdateMixin, CandidacyMixin, PopItApiMixin):
    pass

class TestUpdatePerson(TestCase):

    @patch.object(FakePersonCollection, 'put')
    @patch('candidates.update.invalidate_posts')
    @patch('candidates.update.invalidate_person')
    @patch('candidates.popit.PopIt')
    def test_update_tessa_jowell(
            self,
            mock_popit,
            mock_invalidate_person,
            mock_invalidate_posts,
            mocked_put
    ):

        mock_popit.return_value.organizations = FakeOrganizationCollection
        mock_popit.return_value.persons = FakePersonCollection

        view = MinimalUpdateClass()

        view.create_candidate_list_memberships = MagicMock()
        view.create_party_memberships = MagicMock()

        new_person_data = {
            "birth_date": None,
            "email": "foo@example.org",
            "homepage_url": "http://foo.example.org",
            "id": "2009",
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
                    "name": "Dulwich and West Norwood",
                    "post_id": "65808",
                },
                "2015": {
                    "mapit_url": "http://mapit.mysociety.org/area/65808",
                    "name": "Dulwich and West Norwood",
                    "post_id": "65808",
                }
            },
            "twitter_username": "jowellt",
            "wikipedia_url": "",
        }

        # This is for the previous versions array; just include the
        # fields we need to notice a change in posts that should be
        # invalidated:
        previous_version = {
            'data': {
                "standing_in": {
                    "2010": {
                        "mapit_url": "http://mapit.mysociety.org/area/65808",
                        "name": "Dulwich and West Norwood",
                        "post_id": "65808",
                    },
                    "2015": {
                        "mapit_url": "http://mapit.mysociety.org/area/65913",
                        "name": "Camberwell and Peckham",
                        "post_id": "65913",
                    }
                },
            }
        }

        view.update_person(
            new_person_data,
            {
                'information_source': 'A change made for testing purposes',
                'username': 'tester',
                'version_id': '6054aa38b30b4418',
                'timestamp': '2014-09-28T14:02:44.567413',
            },
            [previous_version]
        )
        # FIXME: really we should only need the second call here, but
        # see the FIXME in candidates/update.py:

        self.assertEqual(2, len(mocked_put.call_args_list))

        first_put_call_args = {
                'birth_date': None,
                'contact_details': [],
                'email': u'foo@example.org',
                'gender': None,
                'honorific_prefix': None,
                'honorific_suffix': None,
                'name': u'Tessa Jowell',
                'links': [],
                'other_names': [],
                'party_memberships': None,
                'standing_in': None,
                'versions': [
                    {
                        'username': 'tester',
                        'information_source': 'A change made for testing purposes',
                        'version_id': '6054aa38b30b4418',
                        'timestamp': '2014-09-28T14:02:44.567413',
                        'data': new_person_data
                    },
                    previous_version
                ],
            }

        second_put_call_args = {
                'birth_date': None,
                'contact_details': [
                    {
                        'type': 'twitter',
                        'value': 'jowellt'
                    }
                ],
                'email': u'foo@example.org',
                'gender': None,
                'honorific_prefix': None,
                'honorific_suffix': None,
                'name': u'Tessa Jowell',
                'links': [
                    {
                        'note': 'homepage',
                        'url': 'http://foo.example.org'
                    }
                ],
                'party_memberships': {
                    '2010': {
                        'id': 'party:53',
                        'name': 'Labour Party'
                    },
                    '2015': {
                        'id': 'party:53',
                        'name': 'Labour Party'
                    }
                },
                'standing_in': {
                    '2015': {
                        'name': 'Dulwich and West Norwood',
                        'mapit_url': 'http://mapit.mysociety.org/area/65808',
                        'post_id': '65808',
                    },
                    '2010': {
                        'name': 'Dulwich and West Norwood',
                        'mapit_url': 'http://mapit.mysociety.org/area/65808',
                        'post_id': '65808',
                    }
                },
                'versions': [
                    {
                        'username': 'tester',
                        'information_source': 'A change made for testing purposes',
                        'version_id': '6054aa38b30b4418',
                        'timestamp': '2014-09-28T14:02:44.567413',
                        'data': new_person_data
                    },
                    previous_version
                ],
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
            '2009',
            new_person_data,
        )
        view.create_party_memberships.assert_called_once_with(
            '2009',
            new_person_data
        )

        mock_invalidate_person.assert_called_with('2009')
        mock_invalidate_posts.assert_called_with(set(['65808', '65913']))
