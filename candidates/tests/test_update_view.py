from urlparse import urlsplit

from mock import patch

from django_webtest import WebTest

from .auth import TestUserMixin
from .helpers import equal_call_args
from .fake_popit import get_example_popit_json, FakePersonCollection

example_timestamp = '2014-09-29T10:11:59.216159'
example_version_id = '5aa6418325c1a0bb'

@patch('candidates.popit.PopIt')
class TestUpdatePersonView(TestUserMixin, WebTest):

    def test_update_person_view_get_without_login(self, mock_popit):
        response = self.app.get('/person/2009/update')
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual('/accounts/login/', split_location.path)
        self.assertEqual('next=/person/2009/update', split_location.query)

    @patch('candidates.views.people.UpdatePersonView.get_person')
    def test_update_person_view_get(self, mock_get_person, mock_popit):
        mock_popit.return_value.persons = FakePersonCollection
        mock_get_person.return_value = (
            get_example_popit_json('persons_2009_ynmp.json'),
            {}
        )
        # For the moment just check that the form's actually there:
        response = self.app.get('/person/2009/update', user=self.user)
        response.forms['person-details']

    @patch('candidates.views.people.UpdatePersonView.get_current_timestamp')
    @patch('candidates.views.people.UpdatePersonView.create_version_id')
    @patch('candidates.views.people.UpdatePersonView.update_person')
    @patch('candidates.views.people.UpdatePersonView.get_person')
    def test_update_person_submission(
            self,
            mock_get_person,
            mock_update_person,
            mock_create_version_id,
            mock_get_current_timestamp,
            mock_popit):
        mock_popit.return_value.persons = FakePersonCollection
        mock_get_current_timestamp.return_value = example_timestamp
        mock_create_version_id.return_value = example_version_id
        mock_get_person.return_value = (
            get_example_popit_json('persons_2009_ynmp.json'),
            {}
        )
        response = self.app.get('/person/2009/update', user=self.user)
        form = response.forms['person-details']
        form['wikipedia_url'] = 'http://en.wikipedia.org/wiki/Tessa_Jowell'
        form['party_gb'] = 'party:90'
        form['party_ni'] = 'party:none'
        form['source'] = "Some source of this information"
        submission_response = form.submit()
        self.assertTrue(mock_update_person.called)

        expected_call_args = (
            {
                'birth_date': None,
                'email': 'jowell@example.com',
                'facebook_page_url': '',
                'facebook_personal_url': '',
                'gender': '',
                'homepage_url': '',
                'honorific_prefix': '',
                'honorific_suffix': '',
                'id': '2009',
                'linkedin_url': '',
                'name': 'Tessa Jowell',
                'standing_in': {
                    '2015': {
                        'name': 'Dulwich and West Norwood',
                        'mapit_url': 'http://mapit.mysociety.org/area/65808',
                        'post_id': '65808',
                    },
                    '2010': {
                        'name': 'Dulwich and West Norwood',
                        'mapit_url': 'http://mapit.mysociety.org/area/65808',
                        "post_id": "65808"
                    }
                },
                'party_memberships': {
                    '2015': {
                        'id': 'party:90',
                        'name': 'Liberal Democrats'
                    },
                    '2010': {
                        'id': 'party:53',
                        'name': 'Labour Party'
                    }
                },
                'party_ppc_page_url': '',
                'twitter_username': '',
                'wikipedia_url': 'http://en.wikipedia.org/wiki/Tessa_Jowell',
            },
            {
                'information_source': 'Some source of this information',
                'username': 'john',
                'version_id': example_version_id,
                'timestamp': example_timestamp,
            },
            []
        )

        self.assertTrue(
            equal_call_args(
                expected_call_args,
                mock_update_person.call_args[0]
            ),
            "update_person was called with unexpected values"
        )

        # It should redirect back to the same person's page:
        split_location = urlsplit(submission_response.location)
        self.assertEqual(
            '/person/2009',
            split_location.path
        )
