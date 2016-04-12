# -*- coding: utf-8 -*-

from . import factories

class UK2015ExamplesMixin(object):

    def setUp(self):
        super(UK2015ExamplesMixin, self).setUp()
        self.wmc_area_type = factories.AreaTypeFactory.create()
        self.gb_parties = factories.PartySetFactory.create(
            slug='gb', name='Great Britain'
        )
        self.ni_parties = factories.PartySetFactory.create(
            slug='ni', name='Northern Ireland'
        )
        self.commons = factories.ParliamentaryChamberFactory.create()
        # Create the 2010 and 2015 general elections:
        self.election = factories.ElectionFactory.create(
            slug='2015',
            name='2015 General Election',
            area_types=(self.wmc_area_type,)
        )
        self.earlier_election = factories.EarlierElectionFactory.create(
            slug='2010',
            name='2010 General Election',
            area_types=(self.wmc_area_type,)
        )
        # Create some example parties:
        factories.PartyFactory.reset_sequence()
        factories.PartyExtraFactory.reset_sequence()
        parties_extra = [
            factories.PartyExtraFactory.create()
            for i in range(4)
        ]
        for party_extra in parties_extra:
            self.gb_parties.parties.add(party_extra.base)
        self.labour_party_extra, self.ld_party_extra, \
            self.green_party_extra, self.conservative_party_extra = \
            parties_extra
        self.sinn_fein_extra = factories.PartyExtraFactory.create(
            slug='party:39',
            base__name='Sinn Féin',
        )
        self.ni_parties.parties.add(self.sinn_fein_extra.base)
        # Create some example posts as well:
        factories.PostFactory.reset_sequence()
        factories.PostExtraFactory.reset_sequence()
        posts_extra = []
        for cons in factories.EXAMPLE_CONSTITUENCIES:
            area_extra = factories.AreaExtraFactory.create(
                base__identifier=cons['id'],
                base__name=cons['name'],
                type=self.wmc_area_type,
            )
            label = 'Member of Parliament for {0}'.format(cons['name'])
            posts_extra.append(factories.PostExtraFactory.create(
                elections=(self.election, self.earlier_election),
                base__organization=self.commons,
                base__area=area_extra.base,
                slug=cons['id'],
                base__label=label,
                party_set=self.gb_parties,
            ))
        self.edinburgh_east_post_extra, self.edinburgh_north_post_extra, \
            self.dulwich_post_extra, self.camberwell_post_extra = posts_extra
