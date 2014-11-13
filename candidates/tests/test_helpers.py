from django.test import TestCase

from ..views import CandidacyMixin

class TestOrganizationToArea(TestCase):

    def test_get_area_from_post_id(self):
        api = CandidacyMixin()
        area = api.get_area_from_post_id('14399')
        self.assertEqual(
            area,
            {'id': 'http://mapit.mysociety.org/area/14399',
             'post_id': '14399',
             'name': 'Aberdeen South'}
        )

    def test_get_area_from_post_id_custom_id(self):
        api = CandidacyMixin()
        area = api.get_area_from_post_id('14399', mapit_url_key='mapit_url')
        self.assertEqual(
            area,
            {'mapit_url': 'http://mapit.mysociety.org/area/14399',
             'post_id': '14399',
             'name': 'Aberdeen South'}
        )

    def test_get_area_from_post_id_unknown_constituency(self):
        api = CandidacyMixin()
        with self.assertRaises(Exception):
            api.get_area_from_post_id('123456789')
