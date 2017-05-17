# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import timedelta
from os.path import join

from django.conf import settings
from django.test import TestCase

from candidates.models import PersonExtra, ImageExtra, PersonRedirect
from ..csv_helpers import list_to_csv

from . import factories
from .auth import TestUserMixin
from .dates import date_in_near_future, FOUR_YEARS_IN_DAYS
from .uk_examples import UK2015ExamplesMixin


def get_person_extra_with_joins(person_id):
    return PersonExtra.objects.joins_for_csv_output().get(pk=person_id)


class CSVTests(TestUserMixin, UK2015ExamplesMixin, TestCase):

    def setUp(self):
        super(CSVTests, self).setUp()
        example_image_filename = join(
            settings.BASE_DIR, 'moderation_queue', 'tests', 'example-image.jpg'
        )
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
        ImageExtra.objects.create_from_file(
            example_image_filename,
            'images/jowell-pilot.jpg',
            base_kwargs={
                'content_object': self.gb_person_extra,
                'is_primary': True,
                'source': 'Taken from Wikipedia',
            },
            extra_kwargs={
                'copyright': 'example-license',
                'uploading_user': self.user,
                'user_notes': 'A photo of Tessa Jowell',
            },
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
        person_extra = get_person_extra_with_joins(self.gb_person_extra.id)
        # After the select_related and prefetch_related calls
        # PersonExtra there should only be one more query - that to
        # find the complex fields mapping:
        with self.assertNumQueries(1):
            person_dict_list = person_extra.as_list_of_dicts(self.election)
        self.assertEqual(len(person_dict_list), 1)
        person_dict = person_dict_list[0]
        self.assertEqual(len(person_dict), 32)
        self.assertEqual(person_dict['id'], 2009)

    def test_as_dict_2010(self):
        person_extra = get_person_extra_with_joins(self.gb_person_extra.id)
        # After the select_related and prefetch_related calls
        # PersonExtra there should only be one more query - that to
        # find the complex fields mapping:
        with self.assertNumQueries(1):
            person_dict_list = person_extra.as_list_of_dicts(self.earlier_election)
        self.assertEqual(len(person_dict_list), 1)
        person_dict = person_dict_list[0]
        self.assertEqual(len(person_dict), 32)
        self.assertEqual(person_dict['id'], 2009)

    def test_csv_output(self):
        tessa_image_url = self.gb_person_extra.primary_image().url
        d = {
            'election_date': date_in_near_future,
            'earlier_election_date': date_in_near_future - timedelta(days=FOUR_YEARS_IN_DAYS),
        }
        PersonRedirect.objects.create(old_person_id=12, new_person_id=1953)
        PersonRedirect.objects.create(old_person_id=56, new_person_id=1953)
        example_output = (
            'id,name,honorific_prefix,honorific_suffix,gender,birth_date,election,party_id,party_name,post_id,post_label,mapit_url,elected,email,twitter_username,facebook_page_url,party_ppc_page_url,facebook_personal_url,homepage_url,wikipedia_url,linkedin_url,image_url,proxy_image_url_template,image_copyright,image_uploading_user,image_uploading_user_notes,twitter_user_id,election_date,election_current,party_lists_in_use,party_list_position,old_person_ids\r\n'
            '2009,Tessa Jowell,Ms,DBE,female,,2015,party:53,Labour Party,65913,Camberwell and Peckham,http://mapit.mysociety.org/area/65913,,jowell@example.com,,,,,,,,{image_url},,example-license,john,A photo of Tessa Jowell,,{election_date},True,False,,\r\n'.format(image_url=tessa_image_url, **d) + \
            '2009,Tessa Jowell,Ms,DBE,female,,2010,party:53,Labour Party,65808,Dulwich and West Norwood,http://mapit.mysociety.org/area/65808,,jowell@example.com,,,,,,,,{image_url},,example-license,john,A photo of Tessa Jowell,,{earlier_election_date},False,False,,\r\n'.format(image_url=tessa_image_url, **d) + \
            '1953,Daith\xed McKay,,,male,,2015,party:39,Sinn F\xe9in,66135,North Antrim,http://mapit.mysociety.org/area/66135,,,,,,,,,,,,,,,,{election_date},True,False,,12;56\r\n'.format(**d) + \
            '1953,Daith\xed McKay,,,male,,2010,party:39,Sinn F\xe9in,66135,North Antrim,http://mapit.mysociety.org/area/66135,,,,,,,,,,,,,,,,{earlier_election_date},False,False,,12;56\r\n'.format(**d)
        )
        gb_person_extra = get_person_extra_with_joins(self.gb_person_extra.id)
        ni_person_extra = get_person_extra_with_joins(self.ni_person_extra.id)
        # After the select_related and prefetch_related calls on
        # PersonExtra, there should only be one query per PersonExtra:
        redirects = PersonRedirect.all_redirects_dict()
        with self.assertNumQueries(2):
            list_of_dicts = gb_person_extra.as_list_of_dicts(
                None, redirects=redirects)
            list_of_dicts += ni_person_extra.as_list_of_dicts(
                None, redirects=redirects)
        self.assertEqual(list_to_csv(list_of_dicts), example_output)
