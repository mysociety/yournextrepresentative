from urlparse import urlsplit

from mock import patch

from django_webtest import WebTest

from .auth import TestUserMixin
from .helpers import equal_call_args
from .fake_popit import (
    get_example_popit_json,
    FakeOrganizationCollection, FakePersonCollection
)
from ..models import LoggedAction

example_timestamp = '2014-09-29T10:11:59.216159'
example_version_id = '5aa6418325c1a0bb'

def fill_form(form, form_dict):
    for key, value in form_dict.items():
        form[key] = value

@patch('candidates.popit.PopIt')
class TestNewPersonView(TestUserMixin, WebTest):

    @patch('candidates.views.people.NewPersonView.get_current_timestamp')
    @patch('candidates.views.people.NewPersonView.create_version_id')
    @patch('candidates.views.people.NewPersonView.create_person')
    def test_new_person_submission(
            self,
            mock_create_person,
            mock_create_version_id,
            mock_get_current_timestamp,
            mock_popit):
        # Get the constituency page:
        mock_popit.return_value.organizations = FakeOrganizationCollection
        mock_popit.return_value.persons = FakePersonCollection
        # Just a smoke test for the moment:
        response = self.app.get(
            '/constituency/65808/dulwich-and-west-norwood',
            user=self.user
        )
        mock_get_current_timestamp.return_value = example_timestamp
        mock_create_version_id.return_value = example_version_id
        # Get the add candidate form and fill in some values:
        form = response.forms['new-candidate-form']
        form_dict = {
            'name': 'Jane Doe',
            # Make Jane Doe be standing for the Monster Raving Loony
            # Party in Dulwich and West Norwood:
            'party_gb': 'party:66',
            'party_ni': 'party:none',
            'constituency': '65808',
            'email': 'jane@example.com',
            'wikipedia_url': 'http://en.wikipedia.org/wiki/Jane_Doe',
        }
        fill_form(form, form_dict)
        submission_response = form.submit()
        # If there's no source specified, it shouldn't ever get to
        # update_person, and redirect back to the constituency page:
        self.assertEqual(0, mock_create_person.call_count)

        mock_create_person.return_value = '12345'

        # Try again with the source field filled in:
        form['source'] = 'A test new person, source: http://example.org'
        submission_response = form.submit()

        expected_call_args = (
            {
                'birth_date': None,
                'email': u'jane@example.com',
                'facebook_page_url': '',
                'facebook_personal_url': '',
                'gender': '',
                'homepage_url': u'',
                'honorific_prefix': '',
                'honorific_suffix': '',
                'linkedin_url': u'',
                'name': u'Jane Doe',
                'party_memberships': {
                    '2015': {
                        'name': u'Official Monster Raving Loony Party',
                        'id': 'party:66'
                    }
                },
                'party_ppc_page_url': '',
                'standing_in': {
                    '2015': {
                        'name': u'Dulwich and West Norwood',
                        'mapit_url': 'http://mapit.mysociety.org/area/65808',
                        'post_id': '65808'
                    }
                },
                'twitter_username': u'',
                'wikipedia_url': u'http://en.wikipedia.org/wiki/Jane_Doe',
            },
            {
                'information_source': u'A test new person, source: http://example.org',
                'timestamp': example_timestamp,
                'username': u'john',
                'version_id': example_version_id,
            }
        )

        self.assertTrue(
            equal_call_args(
                expected_call_args,
                mock_create_person.call_args[0]
            ),
            "create_person was called with unexpected values"
        )

        split_location = urlsplit(submission_response.location)
        self.assertEqual(
            '/person/12345',
            split_location.path
        )

        # Find the most recent action in the actions table, and check
        # that it corresponds to this creation:
        last_logged_action = LoggedAction.objects.all().order_by('-created')[0]
        self.assertEqual(
            last_logged_action.popit_person_id,
            '12345',
        )
        self.assertEqual(
            last_logged_action.popit_person_new_version,
            example_version_id,
        )
        self.assertEqual(
            last_logged_action.action_type,
            'person-create'
        )
