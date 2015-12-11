# -*- coding: utf-8 -*-

from mock import patch, Mock

from urlparse import urlsplit

from nose.plugins.attrib import attr
from django_webtest import WebTest
from django.test.utils import override_settings

from candidates.tests.factories import (
    PostExtraFactory,
    ParliamentaryChamberFactory, PartySetFactory, AreaExtraFactory
)
from elections.models import Election

def fake_requests_for_mapit(url):
    """Return reduced MapIt output for some known URLs"""
    if url == 'http://mapit.mysociety.org/postcode/sw1a1aa':
        status_code = 200
        json_result = {
            "shortcuts": {
                "WMC": 65759,
            },
        }
    elif url == 'http://mapit.mysociety.org/postcode/se240ag':
        status_code = 200
        json_result = {
            "shortcuts": {
                "WMC": "65808",
            },
        }
    elif url == 'http://mapit.mysociety.org/postcode/cb28rq':
        status_code = 404
        json_result = {
            "code": 404,
            "error": "No Postcode matches the given query."
        }
    elif url == 'http://mapit.mysociety.org/postcode/foobar':
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
@patch('elections.uk_general_election_2015.mapit.requests')
class TestConstituencyPostcodeFinderView(WebTest):
    def setUp(self):
        election = Election.objects.get(slug='2015')
        wmc_area_type = election.area_types.get(name='WMC')
        gb_parties = PartySetFactory.create(slug='gb', name='Great Britain')
        commons = ParliamentaryChamberFactory.create()
        area_extra = AreaExtraFactory.create(
            base__name="Dulwich and West Norwood",
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
        response.forms['form-name']

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
            '/election/2015/post/65808/dulwich-and-west-norwood',
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
        form['postcode'] = u'SW1A 1ӔA'
        response = form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            u'There were disallowed characters in &quot;SW1A 1ӔA&quot;',
            response
        )


@attr(country='uk')
class TestConstituencyNameListFinderView(WebTest):
    def setUp(self):
        election = Election.objects.get(slug='2015')
        wmc_area_type = election.area_types.get(name='WMC')
        gb_parties = PartySetFactory.create(slug='gb', name='Great Britain')
        commons = ParliamentaryChamberFactory.create()
        area_extra = AreaExtraFactory.create(
            base__name="Dulwich and West Norwood",
            type=wmc_area_type,
        )
        self.area = area_extra.base
        PostExtraFactory.create(
            elections=(election,),
            base__organization=commons,
            slug='65808',
            base__label='Member of Parliament for Dulwich and West Norwood',
            party_set=gb_parties,
            base__area=self.area,
        )

    def test_pick_constituency_name(self):
        response = self.app.get('/')
        form = response.forms['form-name']
        form['constituency'] = self.area.id
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual(
            split_location.path,
            '/election/2015/post/65808/dulwich-and-west-norwood'
        )

    def test_post_no_constituency_selected(self):
        response = self.app.get('/')
        form = response.forms['form-name']
        form['constituency'] = ''
        response = form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertIn('This field is required', response)

    def test_post_invalid_constituency_id(self):
        response = self.app.post(
            '/lookup/name',
            {
                'constituency': 'made-up-555',
            }
        )
        self.assertIn(
            'Select a valid choice. That choice is not one of the available choices.',
            response
        )


@attr(country='uk')
@override_settings(MAPIT_TYPES=['WMC'])
@override_settings(MAPIT_CURRENT_GENERATION='22')
@patch('elections.uk_general_election_2015.mapit.requests')
class TestConstituencyNameFinderView(WebTest):
    def setUp(self):
        election = Election.objects.get(slug='2015')
        wmc_area_type = election.area_types.get(name='WMC')
        gb_parties = PartySetFactory.create(slug='gb', name='Great Britain')
        commons = ParliamentaryChamberFactory.create()
        area_extra = AreaExtraFactory.create(
            base__name="Dulwich and West Norwood",
            type=wmc_area_type,
        )
        self.area = area_extra.base
        PostExtraFactory.create(
            elections=(election,),
            base__organization=commons,
            slug='65808',
            base__label='Member of Parliament for Dulwich and West Norwood',
            party_set=gb_parties,
            base__area=self.area,
        )

    def test_pick_constituency_name(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_mapit
        response = self.app.get('/')
        form = response.forms['form-postcode']
        form['postcode'] = 'SE24 0AG'
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual(
            split_location.path,
            '/election/2015/post/65808/dulwich-and-west-norwood'
        )
