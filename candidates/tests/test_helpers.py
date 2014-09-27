from django.test import TestCase

from mock import patch

from ..views import PopItApiMixin

class TestOrganizationToArea(TestCase):

    # We have to mock PopIt in these tests otherwise it'll try to
    # contact the server on creating that object - it wouldn't
    # otherwise be called.

    @patch('candidates.views.PopIt')
    def test_get_area_from_organization(self, mock_popit):
        api = PopItApiMixin()
        area = api.get_area_from_organization({
            'classification': 'Candidate List',
            'name': 'Candidates for Aberdeen South in 2010',
        })
        self.assertEqual(
            area,
            {'id': 'http://mapit.mysociety.org/area/14399',
             'name': 'Aberdeen South'}
        )

    @patch('candidates.views.PopIt')
    def test_get_area_from_organization_custom_id(self, mock_popit):
        api = PopItApiMixin()
        area = api.get_area_from_organization({
            'classification': 'Candidate List',
            'name': 'Candidates for Aberdeen South in 2010',
        }, mapit_url_key='mapit_url')
        self.assertEqual(
            area,
            {'mapit_url': 'http://mapit.mysociety.org/area/14399',
             'name': 'Aberdeen South'}
        )

    @patch('candidates.views.PopIt')
    def test_get_area_from_organization_malformed(self, mock_popit):
        api = PopItApiMixin()
        with self.assertRaises(Exception):
            api.get_area_from_organization({
                'classification': 'Candidate List',
                'name': 'Candidates for Aberdeen South',
            })

    @patch('candidates.views.PopIt')
    def test_get_area_from_organization_wrong_classification(self, mock_popit):
        api = PopItApiMixin()
        area = api.get_area_from_organization({
            'classification': 'List of People',
            'name': 'Candidates for Aberdeen South in 2010',
        })
        self.assertIsNone(area)

    @patch('candidates.views.PopIt')
    def test_get_area_from_organization_unknown_constituency(self, mock_popit):
        api = PopItApiMixin()
        with self.assertRaises(Exception):
            api.get_area_from_organization({
                'classification': 'Candidate List',
                'name': 'Candidates for Ambridge in 2010',
            })
