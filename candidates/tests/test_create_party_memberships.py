from django.test import TestCase

from mock import call, patch, MagicMock

from .fake_popit import (
    fake_get_result,
    FakePersonCollection, FakeOrganizationCollection
)
from ..views import PersonUpdateMixin, CandidacyMixin, PopItApiMixin

class MinimalUpdateClass(PersonUpdateMixin, CandidacyMixin, PopItApiMixin):
    pass

# FIXME: should this really be calling POST outside the
# create_with_id_retries? Probably not...

def fake_org_post(data):
    raise Exception("Unknown organization POST: " + data)

class TestCreatePerson(TestCase):

    @patch.object(FakeOrganizationCollection, 'post')
    @patch('candidates.popit.PopIt')
    def test_create_party_memberships(self, mock_popit, mock_org_post):

        mock_popit.return_value.organizations = FakeOrganizationCollection
        mock_popit.return_value.persons = FakePersonCollection

        mock_org_post.side_effect = fake_org_post

        view = MinimalUpdateClass()

        person_data = {
            "birth_date": None,
            "email": "jane@example.org",
            "homepage_url": "http://janedoe.example.org",
            "id": "jane-doe",
            "name": "Jane Doe",
            "party_memberships": {
                "2010": {
                    "id": "party:53",
                    "name": "Labour Party"
                },
                "2015": {
                    "id": "party:52",
                    "name": "Conservative Party"
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

        view.create_party_memberships('jane-doe', person_data)

        # The last two calls to mock_popit should be creation of the
        # memberships:

        expected_calls = [
            call().memberships.post({
                'organization_id': 'party:53',
                'person_id': 'jane-doe',
                'start_date': '2005-05-06',
                'end_date': '2010-05-06'
            }),
            call().memberships.post({
                'organization_id': 'party:52',
                'person_id': 'jane-doe',
                'start_date': '2010-05-07',
                'end_date': '9999-12-31'
            })
        ]

        mock_popit.assert_has_calls(expected_calls, any_order=True)

        # There should be no attempt to create a new organization:
        self.assertEqual(0, len(mock_org_post.call_args_list))
