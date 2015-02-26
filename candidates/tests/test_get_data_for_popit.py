from django.test import TestCase

from candidates.models import get_person_data_from_dict

# All these are essentially tests for get_person_data_from_dict

class TestGetDataForPopIt(TestCase):

    def test_get_person_data_from_dict(self):
        form_data = {
            'name': 'John Doe',
            'email': 'john@example.org',
            'birth_date': '',
            'wikipedia_url': 'http://en.wikipedia.org/wiki/John_Doe',
            'homepage_url': '',
            'twitter_username': 'foobar',
            'facebook_personal_url': '',
            'facebook_page_url': '',
            'party_ppc_page_url': '',
        }
        expected_result = {
            'birth_date': None,
            'contact_details': [
                {
                    'type': 'twitter',
                    'value': 'foobar'
                }
            ],
            'email': u'john@example.org',
            'gender': None,
            'honorific_prefix': None,
            'honorific_suffix': None,
            'links': [
                {
                    'note': 'wikipedia', 'url': 'http://en.wikipedia.org/wiki/John_Doe'
                }
            ],
            'name': u'John Doe',
        }
        self.assertEqual(
            get_person_data_from_dict(form_data),
            expected_result
        )

    def test_get_person_data_from_dict_clear_email(self):
        form_data = {
            'name': 'John Doe',
            'email': '',
            'birth_date': '',
            'wikipedia_url': 'http://en.wikipedia.org/wiki/John_Doe',
            'homepage_url': '',
            'twitter_username': 'foobar',
            'facebook_personal_url': '',
            'facebook_page_url': '',
            'party_ppc_page_url': '',
        }
        expected_result = {
            'birth_date': None,
            'contact_details': [
                {
                    'type': 'twitter',
                    'value': 'foobar'
                }
            ],
            'email': None,
            'gender': None,
            'honorific_prefix': None,
            'honorific_suffix': None,
            'links': [
                {
                    'note': 'wikipedia', 'url': 'http://en.wikipedia.org/wiki/John_Doe'
                }
            ],
            'name': u'John Doe',
        }
        self.assertEqual(
            get_person_data_from_dict(form_data),
            expected_result
        )
