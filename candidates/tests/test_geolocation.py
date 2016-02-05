# -*- coding: utf-8 -*-

from mock import patch, Mock

from django_webtest import WebTest

from candidates.tests.factories import (
    AreaTypeFactory, ElectionFactory, PostExtraFactory,
    ParliamentaryChamberExtraFactory,
    PartySetFactory, AreaExtraFactory
)


def fake_requests_for_mapit(url):
    """Return reduced MapIt output for some known URLs"""
    if url == 'http://global.mapit.mysociety.org/point/4326/51.5,-0.143207?type=WMC,LAC&generation=22':
        status_code = 200
        json_result = \
            {"65759": {"parent_area": None, "generation_high": 26, "all_names": {}, "id": 65759, "codes": {"gss": "E14000639", "unit_id": "25040"}, "name": "Cities of London and Westminster", "country": "E", "type_name": "UK Parliament constituency", "generation_low": 13, "country_name": "England", "type": "WMC"}}
    elif url == 'http://global.mapit.mysociety.org/point/4326/51.444,-0.09153?type=WMC,LAC&generation=22':
        status_code = 200
        json_result = \
            {"65808": {"parent_area": None, "generation_high": 26, "all_names": {}, "id": 65808, "codes": {"gss": "E14000673", "unit_id": "25031"}, "name": "Dulwich and West Norwood", "country": "E", "type_name": "UK Parliament constituency", "generation_low": 13, "country_name": "England", "type": "WMC"}, "11822": {"parent_area": 2247, "generation_high": 26, "all_names": {}, "id": 11822, "codes": {"gss": "E32000010", "unit_id": "41446"}, "name": "Lambeth and Southwark", "country": "E", "type_name": "London Assembly constituency", "generation_low": 1, "country_name": "England", "type": "LAC"}}
    elif url == 'http://global.mapit.mysociety.org/point/4326/1.5,-0.143207?type=WMC,LAC&generation=22':
        status_code = 200
        json_result = {}
    else:
        status_code = 200
        json_result = {'error': 'There was an error'}
    return Mock(**{
        'json.return_value': json_result,
        'status_code': status_code
    })


@patch('candidates.views.frontpage.requests')
class TestGeolocator(WebTest):

    def setUp(self):
        wmc_area_type = AreaTypeFactory.create()
        lac_area_type = AreaTypeFactory.create(name='LAC')
        gb_parties = PartySetFactory.create(slug='gb', name='Great Britain')
        commons = ParliamentaryChamberExtraFactory.create()
        lac = ParliamentaryChamberExtraFactory.create(slug='lac')

        election = ElectionFactory.create(
            slug='2015',
            name='2015 General Election',
            area_types=(wmc_area_type,),
            organization=commons.base
        )
        election2 = ElectionFactory.create(
            slug='2015-secondary',
            name='2015 Secondary Election',
            area_types=(lac_area_type,),
            organization=lac.base
        )
        area_extra = AreaExtraFactory.create(
            base__name="Westminster",
            type=wmc_area_type,
        )

        PostExtraFactory.create(
            elections=(election,),
            base__organization=commons.base,
            slug='65759',
            base__label='Member of Parliament for Westminster',
            party_set=gb_parties,
            base__area=area_extra.base,
        )

        area_extra = AreaExtraFactory.create(
            base__name="Dulwich and West Norwood",
            type=wmc_area_type,
        )

        PostExtraFactory.create(
            elections=(election,),
            base__organization=commons.base,
            slug='65808',
            base__label='Member of Parliament for Dulwich and West Norwood',
            party_set=gb_parties,
            base__area=area_extra.base,
        )

        area_extra = AreaExtraFactory.create(
            base__name="Lambeth and Southwark",
            type=lac_area_type,
        )

        PostExtraFactory.create(
            elections=(election2,),
            base__organization=commons.base,
            slug='11822',
            base__label='London Assembly Member for Lambeth and Southwark',
            party_set=gb_parties,
            base__area=area_extra.base,
        )

    def test_valid_coords_redirects_to_constituency(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_mapit
        response = self.app.get('/geolocator/-0.143207,51.5')
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.json, {'url': '/areas/WMC-65759'})

    def test_valid_coords_redirects_with_two_elections(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_mapit
        response = self.app.get('/geolocator/-0.09153,51.444')
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.json, {'url': '/areas/LAC-11822,WMC-65808'})

    def test_invalid_coords_returns_error(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_mapit
        response = self.app.get('/geolocator/-0.143207,1.5')
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.json, {'error': 'Your location does not seem to be covered by this site'})

    def test_handles_mapit_error(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_mapit
        response = self.app.get('/geolocator/-0.207,1.5')
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.json, {'error': 'The area lookup returned an error: \'There was an error\''})
