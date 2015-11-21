from mock import patch, MagicMock
import re

from django_webtest import WebTest

from .factories import (
    AreaTypeFactory, ElectionFactory, EarlierElectionFactory,
    CandidacyExtraFactory, ParliamentaryChamberFactory,
    PartyFactory, PartyExtraFactory, PersonExtraFactory,
    PostExtraFactory
)

class TestPartyPages(WebTest):

    def setUp(self):
        wmc_area_type = AreaTypeFactory.create()
        election = ElectionFactory.create(
            slug='2015',
            name='2015 General Election',
            area_types=(wmc_area_type,)
        )
        earlier_election = EarlierElectionFactory.create(
            slug='2010',
            name='2010 General Election',
            area_types=(wmc_area_type,)
        )
        commons = ParliamentaryChamberFactory.create()
        PartyExtraFactory.reset_sequence()
        PartyFactory.reset_sequence()
        parties = {}
        for i in xrange(0, 4):
            party_extra = PartyExtraFactory.create()
            parties[party_extra.slug] = party_extra

        post_extra = PostExtraFactory.create(
            elections=(election, earlier_election,),
            base__organization=commons,
            slug='65672',
            base__label='Member of Parliament for Doncaster North'
        )
        person_extra = PersonExtraFactory.create(
            base__id='3056',
            base__name='Ed Miliband'
        )
        CandidacyExtraFactory.create(
            election=election,
            base__person=person_extra.base,
            base__post=post_extra.base,
            base__on_behalf_of=parties['party:53'].base
        )

        post_extra = PostExtraFactory.create(
            elections=(election, earlier_election,),
            base__organization=commons,
            slug='65719',
            base__label='Member of Parliament for South Shields'
        )
        person_extra = PersonExtraFactory.create(
            base__id='3814',
            base__name='David Miliband'
        )
        CandidacyExtraFactory.create(
            election=earlier_election,
            base__person=person_extra.base,
            base__post=post_extra.base,
            base__on_behalf_of=parties['party:53'].base
        )

    def test_parties_page(self):
        response = self.app.get('/election/2015/parties/')
        ul = response.html.find('ul', {'class': 'party-list'})
        lis = ul.find_all('li')
        self.assertEqual(len(lis), 2)
        for i, t in enumerate((
            ('/election/2015/party/party:52/conservative-party', 'Conservative Party'),
            ('/election/2015/party/party:53/labour-party', 'Labour Party'),
        )):
            expected_url = t[0]
            expected_text = t[1]
            self.assertEqual(lis[i].find('a')['href'], expected_url)
            self.assertEqual(lis[i].find('a').text, expected_text)

    def test_single_party_page(self):
        response = self.app.get('/election/2015/party/party%3A53/labour-party')
        # There are no candidates in Scotland or Wales in our test data:
        self.assertIn(
            u"We don't know of any Labour Party candidates in Scotland so far.",
            unicode(response)
        )
        self.assertIn(
            u"We don't know of any Labour Party candidates in Wales so far.",
            unicode(response)
        )
        # But this should only be showing results from the Great
        # Britain register, so there shouldn't be a similar message
        # for Northern Ireland:
        self.assertNotIn(
            u"We don't know of any Labour Party candidates in Northern Ireland so far.",
            unicode(response)
        )
        # Check there's no mention of David Miliband's constituency
        # (since he's not standing in 2015) and we've not added enough
        # example candidates to reach the threshold where all
        # constituencies should be shown:
        self.assertNotIn(
            u'South Shields',
            unicode(response)
        )
        # But there is an Ed Miliband:
        self.assertTrue(re.search(
            r'(?ms)<a href="/person/3056">Ed Miliband</a>.*is standing in.*' +
            r'<a href="/election/2015/post/65672/doncaster-north">Doncaster North</a></li>',
            unicode(response)
        ))
