from django_webtest import WebTest

from .auth import TestUserMixin
from .factories import (
    AreaTypeFactory, ElectionFactory, EarlierElectionFactory,
    PostFactory, PostExtraFactory, ParliamentaryChamberFactory,
    PersonExtraFactory, CandidacyExtraFactory, PartyExtraFactory,
    PartyFactory, MembershipFactory, MembershipExtraFactory, PartySetFactory
)


class TestConstituencyDetailView(TestUserMixin, WebTest):

    def setUp(self):
        wmc_area_type = AreaTypeFactory.create()
        gb_parties = PartySetFactory.create(slug='gb', name='Great Britain')
        commons = ParliamentaryChamberFactory.create()
        election = ElectionFactory.create(
            slug='2015',
            name='2015 General Election',
            area_types=(wmc_area_type,),
            organization=commons
        )
        post_extra = PostExtraFactory.create(
            elections=(election,),
            base__organization=commons,
            slug='65808',
            base__label='Member of Parliament for Dulwich and West Norwood',
            party_set=gb_parties,
        )
        person_extra = PersonExtraFactory.create(
            base__id='2009',
            base__name='Tessa Jowell'
        )
        PartyFactory.reset_sequence()
        party_extra = PartyExtraFactory.create()
        gb_parties.parties.add(party_extra.base)
        CandidacyExtraFactory.create(
            election=election,
            base__person=person_extra.base,
            base__post=post_extra.base,
            base__on_behalf_of=party_extra.base
            )
        MembershipFactory.create(
            person=person_extra.base,
            organization=party_extra.base
        )

        winner_post_extra = PostExtraFactory.create(
            elections=(election,),
            base__organization=commons,
            slug='14419',
            base__label='Member of Parliament for Edinburgh East',
            party_set=gb_parties,
        )

        edinburgh_candidate = PersonExtraFactory.create(
            base__id='818',
            base__name='Sheila Gilmore'
        )
        edinburgh_winner = PersonExtraFactory.create(
            base__id='5795',
            base__name='Tommy Sheppard'
        )

        CandidacyExtraFactory.create(
            election=election,
            base__person=edinburgh_winner.base,
            base__post=winner_post_extra.base,
            base__on_behalf_of=party_extra.base,
            elected=True,
            )

        CandidacyExtraFactory.create(
            election=election,
            base__person=edinburgh_candidate.base,
            base__post=winner_post_extra.base,
            base__on_behalf_of=party_extra.base
            )
        MembershipFactory.create(
            person=edinburgh_candidate.base,
            organization=party_extra.base
        )
        MembershipFactory.create(
            person=edinburgh_winner.base,
            organization=party_extra.base
        )

    def test_any_constituency_page_without_login(self):
        # Just a smoke test for the moment:
        response = self.app.get('/election/2015/post/65808/dulwich-and-west-norwood')
        response.mustcontain('<a href="/person/2009/tessa-jowell" class="candidate-name">Tessa Jowell</a> <span class="party">Labour Party</span>')
        # There should be no forms on the page if you're not logged in:

        self.assertEqual(0, len(response.forms))

    def test_any_constituency_page(self):
        # Just a smoke test for the moment:
        response = self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user
        )
        response.mustcontain('<a href="/person/2009/tessa-jowell" class="candidate-name">Tessa Jowell</a> <span class="party">Labour Party</span>')
        form = response.forms['new-candidate-form']
        self.assertTrue(form)

    def test_constituency_with_winner(self):
        response = self.app.get('/election/2015/post/14419/edinburgh-east')
        response.mustcontain('<li class="candidates-list__person candidates-list__person__winner">')

