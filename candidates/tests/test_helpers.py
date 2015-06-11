from django.test import TestCase

from candidates.models import get_area_from_post_id

class TestOrganizationToArea(TestCase):

    def test_get_area_from_post_id(self):
        area = get_area_from_post_id('14399')
        self.assertEqual(
            area,
            {'id': 'http://mapit.mysociety.org/area/14399',
             'post_id': '14399',
             'name': 'Aberdeen South'}
        )

    def test_get_area_from_post_id_custom_id(self):
        area = get_area_from_post_id('14399', mapit_url_key='mapit_url')
        self.assertEqual(
            area,
            {'mapit_url': 'http://mapit.mysociety.org/area/14399',
             'post_id': '14399',
             'name': 'Aberdeen South'}
        )

    def test_get_area_from_post_id_unknown_constituency(self):
        with self.assertRaises(Exception):
            get_area_from_post_id('123456789')
