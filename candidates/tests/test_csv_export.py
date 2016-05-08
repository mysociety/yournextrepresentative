# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import timedelta

from django.test import TestCase

from ..csv_helpers import list_to_csv

from . import factories
from .dates import date_in_near_future, FOUR_YEARS_IN_DAYS
from .uk_examples import UK2015ExamplesMixin


class CSVTests(UK2015ExamplesMixin, TestCase):
    def setUp(self):
        super(CSVTests, self).setUp()
        # The second person's name (and party name) have diacritics in
        # them to test handling of Unicode when outputting to CSV.
        self.gb_person_extra = factories.PersonExtraFactory.create(
            base__id=2009,
            base__name='Tessa Jowell',
            base__honorific_suffix='DBE',
            base__honorific_prefix='Ms',
            base__email='jowell@example.com',
            base__gender='female',
        )
        self.ni_person_extra = factories.PersonExtraFactory.create(
            base__id=1953,
            base__name='Daithí McKay',
            base__gender='male',
        )
        camberwell_area_extra = self.camberwell_post_extra.base.area.extra
        camberwell_area_extra.base.other_identifiers.create(
            scheme='mapit-area-url',
            identifier='http://mapit.mysociety.org/area/65913',
        )
        dulwich_area_extra = self.dulwich_post_extra.base.area.extra
        dulwich_area_extra.base.other_identifiers.create(
            scheme='mapit-area-url',
            identifier='http://mapit.mysociety.org/area/65808',
        )
        north_antrim_area_extra = factories.AreaExtraFactory.create(
            base__identifier='66135',
            base__name='North Antrim',
            type=self.wmc_area_type,
        )
        north_antrim_area_extra.base.other_identifiers.create(
            scheme='mapit-area-url',
            identifier='http://mapit.mysociety.org/area/66135',
        )
        north_antrim_post_extra = factories.PostExtraFactory.create(
            elections=(self.election, self.earlier_election),
            base__organization=self.commons,
            base__area=north_antrim_area_extra.base,
            slug='66135',
            base__label='Member of Parliament for North Antrim',
            party_set=self.ni_parties,
        )
        factories.CandidacyExtraFactory.create(
            election=self.election,
            base__person=self.ni_person_extra.base,
            base__post=north_antrim_post_extra.base,
            base__on_behalf_of=self.sinn_fein_extra.base
        )
        factories.CandidacyExtraFactory.create(
            election=self.earlier_election,
            base__person=self.ni_person_extra.base,
            base__post=north_antrim_post_extra.base,
            base__on_behalf_of=self.sinn_fein_extra.base
        )
        factories.CandidacyExtraFactory.create(
            election=self.election,
            base__person=self.gb_person_extra.base,
            base__post=self.camberwell_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base
        )
        factories.CandidacyExtraFactory.create(
            election=self.earlier_election,
            base__person=self.gb_person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base
        )

    def test_as_list_single_dict(self):
        person_dict_list = self.gb_person_extra.as_list_of_dicts(self.election)
        self.assertEqual(len(person_dict_list), 1)
        person_dict = person_dict_list[0]
        self.assertEqual(len(person_dict), 29)
        self.assertEqual(person_dict['id'], 2009)

    def test_as_dict_2010(self):
        # Could do with a person example who changes constituency
        person_dict_list = self.gb_person_extra.as_list_of_dicts(self.earlier_election)
        self.assertEqual(len(person_dict_list), 1)
        person_dict = person_dict_list[0]
        self.assertEqual(len(person_dict), 29)
        self.assertEqual(person_dict['id'], 2009)

    def test_csv_output(self):
        d = {
            'election_date': date_in_near_future,
            'earlier_election_date': date_in_near_future - timedelta(days=FOUR_YEARS_IN_DAYS),
        }
        example_output = (
            b'id,name,honorific_prefix,honorific_suffix,gender,birth_date,election,party_id,party_name,post_id,post_label,mapit_url,elected,email,twitter_username,facebook_page_url,party_ppc_page_url,facebook_personal_url,homepage_url,wikipedia_url,linkedin_url,image_url,proxy_image_url_template,image_copyright,image_uploading_user,image_uploading_user_notes,twitter_user_id,election_date,election_current\r\n'
            b'2009,Tessa Jowell,Ms,DBE,female,,2015,party:53,Labour Party,65913,Camberwell and Peckham,http://mapit.mysociety.org/area/65913,,jowell@example.com,,,,,,,,,,,,,,{election_date},True\r\n'.format(**d) + \
            b'2009,Tessa Jowell,Ms,DBE,female,,2010,party:53,Labour Party,65808,Dulwich and West Norwood,http://mapit.mysociety.org/area/65808,,jowell@example.com,,,,,,,,,,,,,,{earlier_election_date},False\r\n'.format(**d) + \
            b'1953,Daith\xc3\xad McKay,,,male,,2015,party:39,Sinn F\xc3\xa9in,66135,North Antrim,http://mapit.mysociety.org/area/66135,,,,,,,,,,,,,,,,{election_date},True\r\n'.format(**d) + \
            b'1953,Daith\xc3\xad McKay,,,male,,2010,party:39,Sinn F\xc3\xa9in,66135,North Antrim,http://mapit.mysociety.org/area/66135,,,,,,,,,,,,,,,,{earlier_election_date},False\r\n'.format(**d)
        ).decode('utf-8')
        list_of_dicts = self.gb_person_extra.as_list_of_dicts(None)
        list_of_dicts += self.ni_person_extra.as_list_of_dicts(None)
        self.assertEqual(list_to_csv(list_of_dicts), example_output)
