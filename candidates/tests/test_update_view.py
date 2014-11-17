from urlparse import urlsplit

from mock import patch

from django_webtest import WebTest

from .auth import TestUserMixin
from .helpers import equal_call_args
from .fake_popit import get_example_popit_json

example_timestamp = '2014-09-29T10:11:59.216159'
example_version_id = '5aa6418325c1a0bb'

@patch('candidates.popit.PopIt')
class TestUpdatePersonView(TestUserMixin, WebTest):

    def test_update_person_view_get_without_login(self, mock_popit):
        response = self.app.get('/person/tessa-jowell/update')
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual('/accounts/login/', split_location.path)
        self.assertEqual('next=/person/tessa-jowell/update', split_location.query)

    @patch('candidates.views.UpdatePersonView.get_person')
    def test_update_person_view_get(self, mock_get_person, mock_popit):
        mock_get_person.return_value = get_example_popit_json(
            'persons_tessa-jowell_ynmp.json'
        )
        # For the moment just check that the form's actually there:
        response = self.app.get('/person/tessa-jowell/update', user=self.user)
        response.forms['person-details']

    @patch('candidates.views.UpdatePersonView.get_current_timestamp')
    @patch('candidates.views.UpdatePersonView.create_version_id')
    @patch('candidates.views.UpdatePersonView.update_person')
    @patch('candidates.views.UpdatePersonView.get_person')
    def test_update_person_submission(
            self,
            mock_get_person,
            mock_update_person,
            mock_create_version_id,
            mock_get_current_timestamp,
            mock_popit):
        mock_get_current_timestamp.return_value = example_timestamp
        mock_create_version_id.return_value = example_version_id
        mock_get_person.return_value = get_example_popit_json(
            'persons_tessa-jowell_ynmp.json'
        )
        response = self.app.get('/person/tessa-jowell/update', user=self.user)
        form = response.forms['person-details']
        form['wikipedia_url'] = 'http://en.wikipedia.org/wiki/Tessa_Jowell'
        form['party_gb'] = 'party:90'
        form['party_ni'] = 'party:none'
        form['source'] = "Some source of this information"
        submission_response = form.submit()
        self.assertTrue(mock_update_person.called)

        expected_call_args = (
            {
                'date_of_birth': None,
                'email': 'jowell@example.com',
                'facebook_page_url': '',
                'facebook_personal_url': '',
                'homepage_url': '',
                'id': 'tessa-jowell',
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
                'twitter_username': '',
                'wikipedia_url': 'http://en.wikipedia.org/wiki/Tessa_Jowell',
            },
            {
                'information_source': 'Some source of this information',
                'ip': '127.0.0.1',
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

        # It should redirect back to the consituency page:
        split_location = urlsplit(submission_response.location)
        self.assertEqual(
            '/constituency/65808/dulwich-and-west-norwood',
            split_location.path
        )
