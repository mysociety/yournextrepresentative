from __future__ import unicode_literals

from django.test import TestCase

from nose.plugins.attrib import attr

from candidates.models import PersonExtra, PersonRedirect
from candidates.tests import factories
from candidates.tests.uk_examples import UK2015ExamplesMixin


@attr(country='uk')
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
        camberwell_area_extra = self.camberwell_post_extra.base.area.extra
        camberwell_area_extra.base.other_identifiers.create(
            scheme='mapit-area-url',
            identifier='http://mapit.mysociety.org/area/65913',
        )
        camberwell_area_extra.base.other_identifiers.create(
            scheme='gss',
            identifier='E14000615',
        )
        dulwich_area_extra = self.dulwich_post_extra.base.area.extra
        dulwich_area_extra.base.other_identifiers.create(
            scheme='mapit-area-url',
            identifier='http://mapit.mysociety.org/area/65808',
        )
        dulwich_area_extra.base.other_identifiers.create(
            scheme='gss',
            identifier='E14000673',
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
        self.gb_person_extra.base.identifiers.create(
            identifier='uk.org.publicwhip/person/10326',
            scheme='uk.org.publicwhip',
        )
        self.labour_party_extra.base.identifiers.create(
            identifier='PP53',
            scheme='electoral-commission',
        )

    def test_as_list_single_dict(self):
        PersonRedirect.objects.create(old_person_id=33, new_person_id=2009)
        PersonRedirect.objects.create(old_person_id=44, new_person_id=2009)
        person_extra = PersonExtra.objects \
            .joins_for_csv_output().get(pk=self.gb_person_extra.id)
        # After the select_related and prefetch_related calls
        # PersonExtra there should only be one more query - that to
        # find the complex fields mapping:
        redirects = PersonRedirect.all_redirects_dict()
        with self.assertNumQueries(1):
            person_dict_list = person_extra.as_list_of_dicts(
                self.election, redirects=redirects)
        self.assertEqual(len(person_dict_list), 1)
        person_dict = person_dict_list[0]
        self.assertEqual(len(person_dict), 36)
        self.assertEqual(person_dict['id'], 2009)

        # Test the extra CSV fields:
        self.assertEqual(person_dict['gss_code'], 'E14000615')
        self.assertEqual(person_dict['parlparse_id'], 'uk.org.publicwhip/person/10326')
        self.assertEqual(person_dict['theyworkforyou_url'], 'http://www.theyworkforyou.com/mp/10326')
        self.assertEqual(person_dict['party_ec_id'], 'PP53')
        self.assertEqual(person_dict['old_person_ids'], '33;44')
