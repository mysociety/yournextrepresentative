# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from mock import patch, Mock

from django.utils.six.moves.urllib_parse import urlsplit, urljoin
from django.conf import settings

from nose.plugins.attrib import attr
from django_webtest import WebTest

from candidates.tests.factories import (
    AreaTypeFactory, ElectionFactory, PostExtraFactory,
    ParliamentaryChamberFactory, ParliamentaryChamberExtraFactory,
    PartySetFactory, AreaExtraFactory
)
from candidates.tests.settings import SettingsMixin
from elections.models import Election
from .mapit_postcode_results import se240ag_result, sw1a1aa_result


def fake_requests_for_mapit(url):
    """Return reduced MapIt output for some known URLs"""
    if url == urljoin(settings.MAPIT_BASE_URL, '/postcode/sw1a1aa'):
        status_code = 200
        json_result = sw1a1aa_result
    elif url == urljoin(settings.MAPIT_BASE_URL, '/postcode/se240ag'):
        status_code = 200
        json_result = se240ag_result
    elif url == urljoin(settings.MAPIT_BASE_URL, '/postcode/cb28rq'):
        status_code = 404
        json_result = {
            "code": 404,
            "error": "No Postcode matches the given query."
        }
    elif url == urljoin(settings.MAPIT_BASE_URL, '/postcode/foobar'):
        status_code = 400
        json_result = {
            "code": 400,
            "error": "Postcode 'FOOBAR' is not valid."
        }
    else:
        raise Exception("URL that hasn't been mocked yet: " + url)
    return Mock(**{
        'json.return_value': json_result,
        'status_code': status_code
    })

@attr(country='uk')
@patch('elections.uk.mapit.requests')
class TestConstituencyPostcodeFinderView(SettingsMixin, WebTest):
    def setUp(self):
        super(TestConstituencyPostcodeFinderView, self).setUp()
        wmc_area_type = AreaTypeFactory.create()
        gb_parties = PartySetFactory.create(slug='gb', name='Great Britain')
        commons = ParliamentaryChamberFactory.create()
        election = ElectionFactory.create(
            slug='2015',
            name='2015 General Election',
            area_types=(wmc_area_type,),
            organization=commons,
        )
        area_extra = AreaExtraFactory.create(
            base__name="Dulwich and West Norwood",
            base__identifier='gss:E14000673',
            type=wmc_area_type,
        )
        self.area = area_extra.base
        PostExtraFactory.create(
            elections=(election,),
            base__organization=commons,
            slug='65808',
            base__label='Member of Parliament for Dulwich and West Norwood',
            party_set=gb_parties,
            base__area=area_extra.base,
        )

    def test_front_page(self, mock_requests):
        response = self.app.get('/')
        # Check that there is a form on that page
        response.forms['form-postcode']

    def test_valid_postcode_redirects_to_constituency(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_mapit
        response = self.app.get('/')
        form = response.forms['form-postcode']
        form['postcode'] = 'SE24 0AG'
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual(
            split_location.path,
            '/areas/WMC-gss:E14000673',
        )

    def test_valid_postcode_redirects_to_multiple_areas(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_mapit
        # Create some extra posts and areas:
        london_assembly = ParliamentaryChamberExtraFactory.create(
            slug='london-assembly', base__name='London Assembly'
        )
        lac_area_type = AreaTypeFactory.create(name='LAC')
        gla_area_type = AreaTypeFactory.create(name='GLA')
        area_extra_lac = AreaExtraFactory.create(
            base__identifier='gss:E32000010',
            base__name="Dulwich and West Norwood",
            type=lac_area_type,
        )
        area_extra_gla = AreaExtraFactory.create(
            base__identifier='unit_id:41441',
            base__name='Greater London Authority',
            type=gla_area_type,
        )
        election_lac = ElectionFactory.create(
            slug='gb-gla-2016-05-05-c',
            organization=london_assembly.base,
            name='2016 London Assembly Election (Constituencies)',
            area_types=(lac_area_type,),
        )
        election_gla = ElectionFactory.create(
            slug='gb-gla-2016-05-05-a',
            organization=london_assembly.base,
            name='2016 London Assembly Election (Additional)',
            area_types=(gla_area_type,),
        )
        PostExtraFactory.create(
            elections=(election_lac,),
            base__area=area_extra_lac.base,
            base__organization=london_assembly.base,
            slug='11822',
            base__label='Assembly Member for Lambeth and Southwark',
        )
        PostExtraFactory.create(
            elections=(election_gla,),
            base__area=area_extra_gla.base,
            base__organization=london_assembly.base,
            slug='2247',
            base__label='2016 London Assembly Election (Additional)',
        )
        # ----------------------------
        response = self.app.get('/')
        form = response.forms['form-postcode']
        form['postcode'] = 'SE24 0AG'
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual(
            split_location.path,
            '/areas/GLA-unit_id:41441,LAC-gss:E32000010,WMC-gss:E14000673',
        )

    def test_valid_postcode_redirects_to_only_real_areas(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_mapit
        # Create some extra posts and areas:
        london_assembly = ParliamentaryChamberExtraFactory.create(
            slug='london-assembly', base__name='London Assembly'
        )
        lac_area_type = AreaTypeFactory.create(name='LAC')
        gla_area_type = AreaTypeFactory.create(name='GLA')
        area_extra_gla = AreaExtraFactory.create(
            base__identifier='unit_id:41441',
            base__name='Greater London Authority',
            type=gla_area_type,
        )
        ElectionFactory.create(
            slug='gb-gla-2016-05-05-c',
            organization=london_assembly.base,
            name='2016 London Assembly Election (Constituencies)',
            area_types=(lac_area_type,),
        )
        election_gla = ElectionFactory.create(
            slug='gb-gla-2016-05-05-a',
            organization=london_assembly.base,
            name='2016 London Assembly Election (Additional)',
            area_types=(gla_area_type,),
        )
        PostExtraFactory.create(
            elections=(election_gla,),
            base__area=area_extra_gla.base,
            base__organization=london_assembly.base,
            slug='2247',
            base__label='2016 London Assembly Election (Additional)',
        )
        # ----------------------------
        response = self.app.get('/')
        form = response.forms['form-postcode']
        form['postcode'] = 'SE24 0AG'
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual(
            split_location.path,
            '/areas/GLA-unit_id:41441,WMC-gss:E14000673',
        )

    def test_unknown_postcode_returns_to_finder_with_error(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_mapit
        response = self.app.get('/')
        form = response.forms['form-postcode']
        # This looks like a postcode to the usual postcode-checking
        # regular expressions, but doesn't actually exist
        form['postcode'] = 'CB2 8RQ'
        response = form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertIn('The postcode “CB2 8RQ” couldn’t be found', response)

    def test_nonsense_postcode_returns_to_finder_with_error(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_mapit
        response = self.app.get('/')
        form = response.forms['form-postcode']
        # This looks like a postcode to the usual postcode-checking
        # regular expressions, but doesn't actually exist
        form['postcode'] = 'foo bar'
        response = form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertIn('Postcode &#39;FOOBAR&#39; is not valid.', response)

    def test_nonascii_postcode(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_mapit
        response = self.app.get('/')
        form = response.forms['form-postcode']
        # Postcodes with non-ASCII characters should be rejected
        form['postcode'] = 'SW1A 1ӔA'
        response = form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'There were disallowed characters in &quot;SW1A 1ӔA&quot;',
            response
        )
