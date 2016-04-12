from __future__ import unicode_literals

from django.test import TestCase

from candidates.models import PersonExtra, ExtraField

from .auth import TestUserMixin
from .uk_examples import UK2015ExamplesMixin
from . import factories

class TestMissingFields(TestUserMixin, UK2015ExamplesMixin, TestCase):

    def setUp(self):
        super(TestMissingFields, self).setUp()
        slogan_field = ExtraField.objects.create(
            key='slogan',
            type='line',
        )
        person_old_election = factories.PersonExtraFactory.create(
            base__id=100,
            base__name='John Past',
        )
        person_no_details = factories.PersonExtraFactory.create(
            base__id=101,
            base__name='Jane Doe',
        )
        person_empty_slogan = factories.PersonExtraFactory.create(
            base__id=102,
            base__name='John Smith',
            base__birth_date='1999-12-31',
        )
        person_empty_slogan.base.contact_details.create(
            contact_type='twitter',
            value='anothermadeuptwitterusername',
        )
        person_empty_slogan.base.extra_field_values.create(
            field=slogan_field,
            value='',
        )
        person_with_details = factories.PersonExtraFactory.create(
            base__id=103,
            base__name='Joe Bloggs',
            base__birth_date='1980-01-01',
        )
        person_with_details.base.contact_details.create(
            contact_type='twitter',
            value='madeuptwitterusername',
        )
        person_with_details.base.extra_field_values.create(
            field=slogan_field,
            value='Things can only get better',
        )
        factories.CandidacyExtraFactory.create(
            election=self.earlier_election,
            base__person=person_old_election.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base
        )
        factories.CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_no_details.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base
        )
        factories.CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_empty_slogan.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base
        )
        factories.CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_with_details.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.green_party_extra.base
        )

    def test_find_those_missing_dob(self):
        qs = PersonExtra.objects.missing('birth_date')
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs[0].base.name, 'Jane Doe')

    def test_find_those_missing_twitter(self):
        qs = PersonExtra.objects.missing('twitter_username')
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs[0].base.name, 'Jane Doe')

    def test_find_those_missing_slogan(self):
        qs = PersonExtra.objects.missing('slogan').order_by('base__name')
        self.assertEqual(qs.count(), 2)
        self.assertEqual(qs[0].base.name, 'Jane Doe')
        self.assertEqual(qs[1].base.name, 'John Smith')

    def test_non_existent_field(self):
        with self.assertRaises(ValueError):
            PersonExtra.objects.missing('quux')
