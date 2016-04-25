from __future__ import unicode_literals

from django.test import TestCase

from . import factories
from .uk_examples import UK2015ExamplesMixin

class TestPersonLastParty(UK2015ExamplesMixin, TestCase):

    def setUp(self):
        super(TestPersonLastParty, self).setUp()

    def test_both_elections(self):
        person_extra = factories.PersonExtraFactory.create(
            base__id=1234,
            base__name='John Doe',
        )
        factories.CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base,
        )
        factories.CandidacyExtraFactory.create(
            election=self.earlier_election,
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.ld_party_extra.base,
        )
        self.assertEqual(
            person_extra.last_party(),
            self.labour_party_extra.base
        )

    def test_only_earlier(self):
        person_extra = factories.PersonExtraFactory.create(
            base__id=1234,
            base__name='John Doe',
        )
        factories.CandidacyExtraFactory.create(
            election=self.earlier_election,
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.ld_party_extra.base,
        )
        self.assertEqual(
            person_extra.last_party(),
            self.ld_party_extra.base
        )

    def test_only_later(self):
        person_extra = factories.PersonExtraFactory.create(
            base__id=1234,
            base__name='John Doe',
        )
        factories.CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base,
        )
        self.assertEqual(
            person_extra.last_party(),
            self.labour_party_extra.base
        )
