from __future__ import unicode_literals

import re

from django_webtest import WebTest

from .factories import (
    CandidacyExtraFactory, PersonExtraFactory, PostExtraFactory
)
from .uk_examples import UK2015ExamplesMixin

class TestPartyPages(UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestPartyPages, self).setUp()
        constituencies = {}
        for slug, cons_name, country in [
                ('66090', 'Cardiff Central', 'Wales'),
                ('65672', 'Doncaster North', 'England'),
                ('65719', 'South Shields', 'England'),
        ]:
            constituencies[cons_name] = PostExtraFactory.create(
                elections=(self.election, self.earlier_election,),
                base__organization=self.commons,
                slug=slug,
                base__label='Member of Parliament for {0}'.format(cons_name),
                group=country,
            )
        person_extra = PersonExtraFactory.create(
            base__id='3056',
            base__name='Ed Miliband'
        )
        CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_extra.base,
            base__post=constituencies['Doncaster North'].base,
            base__on_behalf_of=self.labour_party_extra.base
        )
        person_extra = PersonExtraFactory.create(
            base__id='3814',
            base__name='David Miliband'
        )
        CandidacyExtraFactory.create(
            election=self.earlier_election,
            base__person=person_extra.base,
            base__post=constituencies['South Shields'].base,
            base__on_behalf_of=self.labour_party_extra.base
        )
        conservative_opponent_extra = PersonExtraFactory.create(
            base__id='6648',
            base__name='Mark Fletcher'
        )
        CandidacyExtraFactory.create(
            election=self.election,
            base__person=conservative_opponent_extra.base,
            base__post=constituencies['South Shields'].base,
            base__on_behalf_of=self.conservative_party_extra.base
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
            "We don't know of any Labour Party candidates in Scotland in the 2015 General Election so far.",
            response.text
        )
        self.assertIn(
            "We don't know of any Labour Party candidates in Wales in the 2015 General Election so far.",
            response.text
        )
        # But this should only be showing results from the Great
        # Britain register, so there shouldn't be a similar message
        # for Northern Ireland:
        self.assertNotIn(
            "We don't know of any Labour Party candidates in Northern Ireland so far.",
            response.text
        )
        # Check there's no mention of David Miliband's constituency
        # (since he's not standing in 2015) and we've not added enough
        # example candidates to reach the threshold where all
        # constituencies should be shown:
        self.assertNotIn(
            'South Shields',
            response.text
        )
        # But there is an Ed Miliband:
        self.assertTrue(re.search(
            r'(?ms)<a href="/person/3056">Ed Miliband</a>\s*is standing in\s*' +
            r'<a href="/election/2015/post/65672/doncaster-north">Doncaster North</a>\s*</li>',
            response.text
        ))
