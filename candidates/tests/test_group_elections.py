from collections import OrderedDict
import datetime

from django.test import TestCase

from elections.models import Election

from .uk_examples import UK2015ExamplesMixin
from .factories import ElectionFactory


class TestElectionGrouping(UK2015ExamplesMixin, TestCase):

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
                                    'role': 'Member of the Scottish Parliament',
                                    'elections': [
                                        {'election': self.sp_c_election},
                                        {'election': self.sp_r_election},
                                    ]
                                }
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
        with self.assertNumQueries(3):
            self.assertEqual(
                Election.group_and_order_elections(include_posts=True),
                [
                    {
                        'current': True,
                        'dates': OrderedDict([
                            (datetime.date(2016, 5, 5), [{
                                'role': 'Member of the Scottish Parliament',
                                'elections': [
                                    {
                                        'posts': [],
                                        'election': self.sp_c_election
                                    },
                                    {
                                        'posts': [],
                                        'election': self.sp_r_election
                                    }
                                ]
                            }]),
                            (self.election.election_date, [{
                                'role': 'Member of Parliament',
                                'elections': [
                                    {
                                        'posts': [
                                            self.camberwell_post_extra,
                                            self.dulwich_post_extra,
                                            self.edinburgh_east_post_extra,
                                            self.edinburgh_north_post_extra,
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
                                        'posts': [
                                            self.camberwell_post_extra,
                                            self.dulwich_post_extra,
                                            self.edinburgh_east_post_extra,
                                            self.edinburgh_north_post_extra,
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
