from django_webtest import WebTest

from . import factories
from .auth import TestUserMixin
from .uk_examples import UK2015ExamplesMixin

class TestPartyDropDownOrdering(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def test_hardly_any_candidates_at_all(self):
        party_choices = self.gb_parties.party_choices()
        self.assertEqual(
            party_choices,
            [
                (u'', u''),
                (self.conservative_party_extra.base.id, u'Conservative Party'),
                (self.green_party_extra.base.id, u'Green Party'),
                (self.labour_party_extra.base.id, u'Labour Party'),
                (self.ld_party_extra.base.id, u'Liberal Democrats'),
            ]
        )

    def create_lots_of_candidates(self, election, parties_and_counts):
        posts_extra = [
            self.edinburgh_east_post_extra,
            self.edinburgh_north_post_extra,
            self.dulwich_post_extra,
            self.camberwell_post_extra,
        ]
        created = 0
        for party, candidates_to_create in parties_and_counts:
            for i in range(candidates_to_create):
                person_id = int("{}00{}".format(election.pk, created + 1))
                pe = factories.PersonExtraFactory.create(
                    base__id=person_id,
                    base__name='John Doe {0}'.format(person_id),
                )
                factories.CandidacyExtraFactory.create(
                    election=election,
                    base__person=pe.base,
                    base__post=posts_extra[created % len(posts_extra)].base,
                    base__on_behalf_of=party.base,
                )
                created += 1

    def test_only_candidates_in_earlier_election(self):
        self.create_lots_of_candidates(
            self.earlier_election,
            (
                (self.labour_party_extra, 16),
                (self.ld_party_extra, 8),
            )
        )
        party_choices = self.gb_parties.party_choices()
        self.assertEqual(
            party_choices,
            [
                (u'', u''),
                (str(self.labour_party_extra.base.id), u'Labour Party (16 candidates)'),
                (str(self.ld_party_extra.base.id), u'Liberal Democrats (8 candidates)'),
                (str(self.conservative_party_extra.base.id), u'Conservative Party'),
                (str(self.green_party_extra.base.id), u'Green Party')
            ],
        )

    def test_enough_candidates_in_current_election(self):
        self.create_lots_of_candidates(
            self.election,
            (
                (self.ld_party_extra, 30),
                (self.green_party_extra, 15),
            )
        )
        party_choices = self.gb_parties.party_choices()
        self.assertEqual(
            party_choices,
            [
                (u'', u''),
                (str(self.ld_party_extra.base.id), u'Liberal Democrats (30 candidates)'),
                (str(self.green_party_extra.base.id), u'Green Party (15 candidates)'),
                (str(self.conservative_party_extra.base.id), u'Conservative Party'),
                (str(self.labour_party_extra.base.id), u'Labour Party'),
            ],
        )

    def test_other_names_in_party_choices(self):
        self.create_lots_of_candidates(
            self.election,
            (
                (self.ld_party_extra, 30),
                (self.green_party_extra, 15),
            )
        )
        self.ld_party_extra.base.other_names.create(
            name="Scottish Liberal Democrats")
        party_choices = self.gb_parties.party_choices()
        self.assertEqual(
            party_choices,
            [
                (u'', u''),
                (
                    u'Liberal Democrats (30 candidates)', [
                        (self.ld_party_extra.base.id,
                        u'Liberal Democrats'),
                        (str(self.ld_party_extra.base.id),
                        u'Scottish Liberal Democrats')
                    ]
                ),
                (
                    str(self.green_party_extra.base.id),
                    u'Green Party (15 candidates)'
                ),
                (
                    str(self.conservative_party_extra.base.id),
                    u'Conservative Party'
                ),
                (
                    str(self.labour_party_extra.base.id),
                    u'Labour Party'
                ),
            ],
        )

    def test_enough_candidates_in_current_election_with_past_election(self):
        self.create_lots_of_candidates(
            self.election,
            (
                (self.ld_party_extra, 30),
                (self.green_party_extra, 15),
            )
        )
        self.create_lots_of_candidates(
            self.earlier_election,
            (
                (self.conservative_party_extra, 30),
                (self.labour_party_extra, 15),
            )
        )
        party_choices = self.gb_parties.party_choices()
        self.assertEqual(
            party_choices,
            [
                (u'', u''),
                (str(self.ld_party_extra.base.id), u'Liberal Democrats (30 candidates)'),
                (str(self.green_party_extra.base.id), u'Green Party (15 candidates)'),
                (str(self.conservative_party_extra.base.id), u'Conservative Party'),
                (str(self.labour_party_extra.base.id), u'Labour Party'),
            ],
        )
