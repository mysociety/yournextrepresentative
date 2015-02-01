from django.test import TestCase

from ..models import PopItPerson
from ..csv_helpers import list_to_csv
from fake_popit import get_example_popit_json


class CSVTests(TestCase):
    def setUp(self):
        person_dict = get_example_popit_json(
                "persons_2009_embed=membership.organization.json")['result']
        self.person = PopItPerson.create_from_dict(person_dict)

    def test_as_list(self):
        person_list = self.person.as_list
        self.assertEqual(len(person_list), 14)
        self.assertEqual(person_list[1], "2959")

    def test_csv_output(self):
        example_output = """name,id,party,constituency,mapit_url,twitter_username,facebook_page_url,party_ppc_page_url,gender,facebook_personal_url,email,homepage_url,wikipedia_url,birth_date\r\nTessa Jowell,2959,Labour Party,Dulwich and West Norwood,http://mapit.mysociety.org/area/65808,,,,,,jowell@example.com,,,\r\n"""
        self.assertEqual(
            list_to_csv([self.person.as_list]),
            example_output,
        )
