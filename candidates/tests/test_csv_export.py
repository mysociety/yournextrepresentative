from django.test import TestCase

from ..models import PopItPerson
from ..csv_helpers import list_to_csv
from fake_popit import get_example_popit_json


class CSVTests(TestCase):
    def setUp(self):
        person_dict = get_example_popit_json(
                "persons_2009_embed=membership.organization.json")['result']
        self.person = PopItPerson.create_from_dict(person_dict)

    def test_as_dict(self):
        person_dict = self.person.as_dict
        self.assertEqual(len(person_dict), 16)
        self.assertEqual(person_dict['id'], "2959")

    def test_csv_output(self):
        example_output = """name,id,party,constituency,mapit_id,mapit_url,gss_code,twitter_username,facebook_page_url,party_ppc_page_url,gender,facebook_personal_url,email,homepage_url,wikipedia_url,birth_date\r\nTessa Jowell,2959,Labour Party,Dulwich and West Norwood,65808,http://mapit.mysociety.org/area/65808,E14000673,,,,,,jowell@example.com,,,\r\n"""
        self.assertEqual(
            list_to_csv([self.person.as_dict]),
            example_output,
        )
