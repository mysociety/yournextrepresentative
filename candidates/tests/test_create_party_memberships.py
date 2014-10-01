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
    if data['id'] == 'new-invented-party':
        return {
            "result": {
                "id": "new-invented-party",
                "classification": "Party",
                "name": "New Invented Party",
                "posts": [],
                "memberships": [],
                "links": [],
                "contact_details": [],
                "identifiers": [],
                "other_names": [],
                "url": "http://candidates.www.127.0.0.1.xip.io:3000/api/v0.1/organizations/new-invented-party",
                "html_url": "http://candidates.www.127.0.0.1.xip.io:3000/organizations/new-invented-party"
            }
        }
    else:
        raise Exception("Unknown organization POST: " + data)

class TestCreatePerson(TestCase):

    @patch.object(FakeOrganizationCollection, 'post')
    @patch('candidates.views.requests')
    @patch('candidates.views.PopIt')
    def test_create_party_memberships(self, mock_popit, mock_requests, mock_org_post):

        mock_requests.get = fake_get_result

        mock_popit.return_value.organizations = FakeOrganizationCollection
        mock_popit.return_value.persons = FakePersonCollection

        mock_org_post.side_effect = fake_org_post

        view = MinimalUpdateClass()

        person_data = {
            "date_of_birth": None,
            "email": "jane@example.org",
            "homepage_url": "http://janedoe.example.org",
            "id": "jane-doe",
            "name": "Jane Doe",
            "party_memberships": {
                "2010": {
                    "id": "labour-party",
                    "name": "Labour Party"
                },
                "2015": {
                    "id": "new-invented-party",
                    "name": "New Invented Party"
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
                'organization_id': 'labour-party',
                'person_id': 'jane-doe',
                'start_date': '2005-05-06',
                'end_date': '2010-05-06'
            }),
            call().memberships.post({
                'organization_id': 'new-invented-party',
                'person_id': 'jane-doe',
                'start_date': '2010-05-07',
                'end_date': '9999-12-31'
            })
        ]

        mock_popit.assert_has_calls(expected_calls, any_order=True)

        self.assertFalse(mock_requests.called)

        mock_org_post.assert_called_once_with({
            'id': 'new-invented-party',
            'classification': 'Party',
            'name': 'New Invented Party'
        })
