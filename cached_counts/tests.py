# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json

from django_webtest import WebTest

from popolo.models import Person

from candidates.tests import factories
from candidates.tests.uk_examples import UK2015ExamplesMixin

from compat import text_type


class CachedCountTestCase(UK2015ExamplesMixin, WebTest):
    maxDiff = None

    def setUp(self):
        super(CachedCountTestCase, self).setUp()
        posts_extra = [
            self.edinburgh_east_post_extra,
            self.edinburgh_north_post_extra,
            self.dulwich_post_extra,
            self.camberwell_post_extra,
        ]
        parties_extra = [
            self.labour_party_extra,
            self.ld_party_extra,
            self.green_party_extra,
            self.conservative_party_extra,
            self.sinn_fein_extra,
        ]
        i = 0
        candidacy_counts = {
            '14419': 10,
            '14420': 3,
            '65808': 5,
            '65913': 0,
        }
        for post_extra in posts_extra:
            candidacy_count = candidacy_counts[post_extra.slug]
            for n in range(candidacy_count):
                person_extra = factories.PersonExtraFactory.create(
                    base__id=str(7000 + i),
                    base__name='Test Candidate {0}'.format(i)
                )
                party = parties_extra[n%5]
                factories.CandidacyExtraFactory.create(
                    election=self.election,
                    base__person=person_extra.base,
                    base__post=post_extra.base,
                    base__on_behalf_of=party.base,
                )
                i += 1
        # Now create a couple of candidacies in the earlier election.
        # First, one sticking with the same party (but in a different
        # post):
        factories.CandidacyExtraFactory.create(
            election=self.earlier_election,
            base__person=Person.objects.get(id=7000),
            base__post=posts_extra[1].base,
            base__on_behalf_of=parties_extra[0].base,
        )
        # Now one in the same post but standing for a different party:
        factories.CandidacyExtraFactory.create(
            election=self.earlier_election,
            base__person=Person.objects.get(id=7001),
            base__post=posts_extra[1].base,
            base__on_behalf_of=parties_extra[2].base,
        )

    def test_reports_top_page(self):
        response = self.app.get('/numbers/')
        self.assertEqual(response.status_code, 200)
        current_div = response.html.find(
            'div', {'id': 'statistics-election-2015'}
        )
        self.assertTrue(current_div)
        self.assertIn('Total candidates: 18', str(current_div))
        earlier_div = response.html.find(
            'div', {'id': 'statistics-election-2010'}
        )
        self.assertIn('Total candidates: 2', str(earlier_div))

    def test_reports_top_page_json(self):
        response = self.app.get('/numbers/?format=json')
        data = json.loads(response.body.decode('utf-8'))
        self.assertEqual(
            data,
            [
                {
                    "current": True,
                    "dates": {
                        text_type(self.election.election_date.isoformat()): [
                            {
                                "elections": [
                                    {
                                        "html_id": "2015",
                                        "id": "2015",
                                        "name": "2015 General Election",
                                        "total": 18
                                    }
                                ],
                                "role": "Member of Parliament"
                            }
                        ],
                        text_type(self.local_election.election_date.isoformat()): [
                            {
                                "elections": [
                                    {
                                        "html_id": "local-maidstone-2016-05-05",
                                        "id": "local.maidstone.2016-05-05",
                                        "name": "Maidstone local election",
                                        "total": 0,
                                    }
                                ],
                                "role": "Local Councillor",
                            },
                        ],
                    }
                },
                {
                    "current": False,
                    "dates": {
                        text_type(self.earlier_election.election_date.isoformat()): [
                            {
                                "elections": [
                                    {
                                        "html_id": "2010",
                                        "id": "2010",
                                        "name": "2010 General Election",
                                        "total": 2
                                    }
                                ],
                                "role": "Member of Parliament"
                            }
                        ]
                    }
                }
            ]
        )

    def test_attention_needed_page(self):
        response = self.app.get('/numbers/attention-needed')
        rows = [
            tuple(td.decode() for td in row.find_all('td'))
            for row in response.html.find_all('tr')
        ]
        self.assertEqual(
            rows,
            [
                ('<td>2015 General Election</td>',
                 '<td><a href="/election/2015/post/65913/camberwell-and-peckham">Member of Parliament for Camberwell and Peckham</a></td>',
                 '<td>0</td>'),
                ('<td>Maidstone local election</td>',
                 '<td><a href="/election/local.maidstone.2016-05-05/post/DIW:E05005004/shepway-south-ward">Shepway South Ward</a></td>',
                 '<td>0</td>'),
                ('<td>2015 General Election</td>',
                 '<td><a href="/election/2015/post/14420/edinburgh-north-and-leith">Member of Parliament for Edinburgh North and Leith</a></td>',
                 '<td>3</td>'),
                ('<td>2015 General Election</td>',
                 '<td><a href="/election/2015/post/65808/dulwich-and-west-norwood">Member of Parliament for Dulwich and West Norwood</a></td>',
                 '<td>5</td>'),
                ('<td>2015 General Election</td>',
                 '<td><a href="/election/2015/post/14419/edinburgh-east">Member of Parliament for Edinburgh East</a></td>',
                 '<td>10</td>')
            ]
        )

    def test_post_counts_page(self):
        response = self.app.get('/numbers/election/2015/posts')
        self.assertEqual(response.status_code, 200)
        rows = [
            tuple(td.decode() for td in row.find_all('td'))
            for row in response.html.find_all('tr')
        ]
        self.assertEqual(
            rows,
            [
                ('<td><a href="/election/2015/post/14419/edinburgh-east">Member of Parliament for Edinburgh East</a></td>',
                 '<td>10</td>'),
                ('<td><a href="/election/2015/post/65808/dulwich-and-west-norwood">Member of Parliament for Dulwich and West Norwood</a></td>',
                 '<td>5</td>'),
                ('<td><a href="/election/2015/post/14420/edinburgh-north-and-leith">Member of Parliament for Edinburgh North and Leith</a></td>',
                 '<td>3</td>'),
                ('<td><a href="/election/2015/post/65913/camberwell-and-peckham">Member of Parliament for Camberwell and Peckham</a></td>',
                 '<td>0</td>'),
            ]
        )

    def test_party_counts_page(self):
        response = self.app.get('/numbers/election/2015/parties')
        self.assertEqual(response.status_code, 200)
        rows = [
            tuple(td.decode() for td in row.find_all('td'))
            for row in response.html.find_all('tr')
        ]
        self.assertEqual(
            rows,
            [
                ('<td><a href="/election/2015/party/party:63/green-party">Green Party</a></td>',
                 '<td>4</td>'),
                ('<td><a href="/election/2015/party/party:53/labour-party">Labour Party</a></td>',
                 '<td>4</td>'),
                ('<td><a href="/election/2015/party/party:90/liberal-democrats">Liberal Democrats</a></td>',
                 '<td>4</td>'),
                ('<td><a href="/election/2015/party/party:52/conservative-party">Conservative Party</a></td>',
                 '<td>3</td>'),
                ('<td><a href="/election/2015/party/party:39/sinn-fein">Sinn F\xe9in</a></td>',
                 '<td>3</td>'),
            ]
        )
