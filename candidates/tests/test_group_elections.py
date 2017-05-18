from collections import OrderedDict
import datetime

from django.test import TestCase

from elections.models import Election

from .uk_examples import UK2015ExamplesMixin
from .factories import ElectionFactory


def get_election_extra(postextra, election):
    return postextra.postextraelection_set.get(
        election=election
    )


class TestElectionGrouping(UK2015ExamplesMixin, TestCase):

    maxDiff = None

    def setUp(self):
        super(TestElectionGrouping, self).setUp()
        self.sp_c_election = ElectionFactory(
            slug='sp.c.2016-05-05',
            name='2016 Scottish Parliament Election (Constituencies)',
            election_date='2016-05-05',
            for_post_role='Member of the Scottish Parliament',
        )
        self.sp_r_election = ElectionFactory(
            slug='sp.r.2016-05-05',
            name='2016 Scottish Parliament Election (Regions)',
            election_date='2016-05-05',
            for_post_role='Member of the Scottish Parliament',
        )

    def test_election_grouping(self):
        with self.assertNumQueries(1):
            self.assertEqual(
                Election.group_and_order_elections(),
                [
                    {
                        'current': True,
                        'dates': OrderedDict([
                            (datetime.date(2016, 5, 5), [
                                {
                                    'role': 'Local Councillor',
                                    'elections': [
                                        {'election': self.local_election},
                                    ]
                                },
                                {
                                    'role': 'Member of the Scottish Parliament',
                                    'elections': [
                                        {'election': self.sp_c_election},
                                        {'election': self.sp_r_election},
                                    ]
                                },
                            ]),
                            (self.election.election_date, [
                                {
                                    'role': 'Member of Parliament',
                                    'elections': [
                                        {'election': self.election}
                                    ]
                                }
                            ])
                        ])
                    },
                    {
                        'current': False,
                        'dates': OrderedDict([
                            (self.earlier_election.election_date, [
                                {
                                    'role': 'Member of Parliament',
                                    'elections': [
                                        {'election':self.earlier_election}
                                    ]
                                }
                            ])
                        ])
                    }
                ]
            )

    def test_election_grouping_with_posts(self):
        camberwell_postextraelection = get_election_extra(
            self.camberwell_post_extra, self.election
        )
        dulwich_postextraelection = get_election_extra(
            self.dulwich_post_extra, self.election
        )
        edinburgh_east_postextraelection = get_election_extra(
            self.edinburgh_east_post_extra, self.election
        )
        edinburgh_north_postextraelection = get_election_extra(
            self.edinburgh_north_post_extra, self.election
        )
        camberwell_earlier = get_election_extra(
            self.camberwell_post_extra, self.earlier_election
        )
        dulwich_earlier = get_election_extra(
            self.dulwich_post_extra, self.earlier_election
        )
        edinburgh_east_earlier = get_election_extra(
            self.edinburgh_east_post_extra, self.earlier_election
        )
        edinburgh_north_earlier = get_election_extra(
            self.edinburgh_north_post_extra, self.earlier_election
        )
        local_council_pee = get_election_extra(
            self.local_post, self.local_election
        )
        with self.assertNumQueries(4):
            self.assertEqual(
                Election.group_and_order_elections(include_postextraelections=True),
                [
                    {
                        'current': True,
                        'dates': OrderedDict([
                            (datetime.date(2016, 5, 5), [{
                                'role': 'Local Councillor',
                                'elections': [
                                    {
                                        'postextraelections': [
                                            local_council_pee
                                        ],
                                        'election': self.local_election,
                                    }
                                ]
                            },
                            {
                                'role': 'Member of the Scottish Parliament',
                                'elections': [
                                    {
                                        'postextraelections': [],
                                        'election': self.sp_c_election
                                    },
                                    {
                                        'postextraelections': [],
                                        'election': self.sp_r_election
                                    }
                                ]
                            }]),
                            (self.election.election_date, [{
                                'role': 'Member of Parliament',
                                'elections': [
                                    {
                                        'postextraelections': [
                                            camberwell_postextraelection,
                                            dulwich_postextraelection,
                                            edinburgh_east_postextraelection,
                                            edinburgh_north_postextraelection,
                                        ],
                                        'election': self.election
                                    }
                                ]
                            }])
                        ])
                    },
                    {
                        'current': False,
                        'dates': OrderedDict([
                            (self.earlier_election.election_date, [{
                                'role': 'Member of Parliament',
                                'elections': [
                                    {
                                        'postextraelections': [
                                            camberwell_earlier,
                                            dulwich_earlier,
                                            edinburgh_east_earlier,
                                            edinburgh_north_earlier,
                                        ],
                                        'election': self.earlier_election
                                    }
                                ]
                            }])
                        ])
                    }
                ]
            )

    def test_election_just_general_elections(self):
        self.sp_c_election.delete()
        self.sp_r_election.delete()
        with self.assertNumQueries(1):
            self.assertEqual(
                Election.group_and_order_elections(),
                [
                    {
                        'current': True,
                        'dates': OrderedDict([
                            (self.local_election.election_date, [{
                                'role': 'Local Councillor', 'elections': [
                                    {'election': self.local_election}
                                ]
                            }]),
                            (self.election.election_date, [{
                                'role': 'Member of Parliament', 'elections': [
                                    {'election': self.election}
                                ]
                            }])
                        ])
                    },
                    {
                        'current': False,
                        'dates': OrderedDict([
                            (self.earlier_election.election_date, [{
                                'role': 'Member of Parliament',
                                'elections': [
                                    {'election': self.earlier_election}
                                ]
                            }])
                        ])
                    }
                ]
            )
