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
        commons_extra = factories.ParliamentaryChamberExtraFactory.create()
        self.commons = commons_extra.base
        # Create the 2010 and 2015 general elections:
        self.election = factories.ElectionFactory.create(
            slug='2015',
            name='2015 General Election',
            for_post_role='Member of Parliament',
            area_types=(self.wmc_area_type,)
        )
        self.earlier_election = factories.EarlierElectionFactory.create(
            slug='2010',
            name='2010 General Election',
            for_post_role='Member of Parliament',
            area_types=(self.wmc_area_type,)
        )
        # Create some example parties:
        factories.PartyFactory.reset_sequence()
        factories.PartyExtraFactory.reset_sequence()
        EXAMPLE_PARTIES = [
            {
                'id': 'party:53',
                'name': 'Labour Party',
                'attr': 'labour_party_extra',
                'party_set': self.gb_parties,
            },
            {
                'id': 'party:90',
                'name': 'Liberal Democrats',
                'attr': 'ld_party_extra',
                'party_set': self.gb_parties,
            },
            {
                'id': 'party:63',
                'name': 'Green Party',
                'attr': 'green_party_extra',
                'party_set': self.gb_parties,
            },
            {
                'id': 'party:52',
                'name': 'Conservative Party',
                'attr': 'conservative_party_extra',
                'party_set': self.gb_parties,
            },
            {
                'id': 'party:39',
                'name': 'Sinn Féin',
                'attr': 'sinn_fein_extra',
                'party_set': self.ni_parties,
            },
        ]
        for party in EXAMPLE_PARTIES:
            p = factories.PartyExtraFactory(
                slug=party['id'],
                base__name=party['name'],
            )
            setattr(self, party['attr'], p)
            party['party_set'].parties.add(p.base)
        # Create some example posts as well:
        EXAMPLE_CONSTITUENCIES = [
            {
                'id': '14419',
                'name': 'Edinburgh East',
                'country': 'Scotland',
                'attr': 'edinburgh_east_post_extra',
            },
            {
                'id': '14420',
                'name': 'Edinburgh North and Leith',
                'country': 'Scotland',
                'attr': 'edinburgh_north_post_extra',
            },
            {
                'id': '65808',
                'name': 'Dulwich and West Norwood',
                'country': 'England',
                'attr': 'dulwich_post_extra',
            },
            {
                'id': '65913',
                'name': 'Camberwell and Peckham',
                'country': 'England',
                'attr': 'camberwell_post_extra',
            },
        ]
        for cons in EXAMPLE_CONSTITUENCIES:
            area_extra = factories.AreaExtraFactory.create(
                base__identifier=cons['id'],
                base__name=cons['name'],
                type=self.wmc_area_type,
            )
            label = 'Member of Parliament for {0}'.format(cons['name'])
            pe = factories.PostExtraFactory.create(
                elections=(self.election, self.earlier_election),
                base__organization=self.commons,
                base__area=area_extra.base,
                slug=cons['id'],
                base__label=label,
                party_set=self.gb_parties,
                group=cons['country'],
            )
            setattr(self, cons['attr'], pe)
            for election in (self.election, self.earlier_election):
                factories.PostExtraElectionFactory.create(
                    postextra=pe,
                    election=election)
