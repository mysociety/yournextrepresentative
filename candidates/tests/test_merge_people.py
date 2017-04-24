from __future__ import unicode_literals

from django.test import TestCase

from ..models import merge_popit_people

class TestMergePeople(TestCase):

    maxDiff = None

    def test_merge_basic_unknown_details(self):
        primary = {
            'foo': 'bar',
            'quux': 'xyzzy',
        }
        secondary = {
            'foo': 'baz',
            'hello': 'goodbye',
        }
        merged = merge_popit_people(primary, secondary)
        self.assertEqual(
            merged,
            {
                'foo': 'bar',
                'quux': 'xyzzy',
                'hello': 'goodbye',
            }
        )

    def test_merge_arrays(self):
        primary = {
            'some-list': ['a', 'b', 'c'],
        }
        secondary = {
            'some-list': ['b', 'c', 'd'],
        }
        merged = merge_popit_people(primary, secondary)
        self.assertEqual(
            merged,
            {
                'some-list': ['a', 'b', 'c', 'd'],
            }
        )

    def test_merge_array_primary_null(self):
        primary = {
            'some-list': None,
        }
        secondary = {
            'some-list': ['a', 'b', 'c'],
        }
        merged = merge_popit_people(primary, secondary)
        self.assertEqual(
            merged,
            {
                'some-list': ['a', 'b', 'c'],
            }
        )

    def test_merge_array_secondary_null(self):
        primary = {
            'some-list': ['a', 'b', 'c'],
        }
        secondary = {
            'some-list': None,
        }
        merged = merge_popit_people(primary, secondary)
        self.assertEqual(
            merged,
            {
                'some-list': ['a', 'b', 'c'],
            }
        )

    def test_merge_standing_in_contradicting(self):
        primary = {
            'standing_in': {
                '2010': {
                    'name': 'Edinburgh East',
                    'post_id': '14419',
                    'mapit_url': 'http://mapit.mysociety.org/area/14419',
                },
                '2015': {
                    'name': 'Edinburgh North and Leith',
                    'post_id': '14420',
                    'mapit_url': 'http://mapit.mysociety.org/area/14420',
                    'elected': True,
                },
            }
        }
        secondary = {
            'standing_in': {
                '2010': {
                    'name': 'Aberdeen South',
                    'post_id': '14399',
                    'mapit_url': 'http://mapit.mysociety.org/area/14399',
                },
                '2015': {
                    'name': 'Aberdeen North',
                    'post_id': '14398',
                    'mapit_url': 'http://mapit.mysociety.org/area/14398',
                },
            },
        }
        merged = merge_popit_people(primary, secondary)
        self.assertEqual(
            merged,
            {
                'standing_in': {
                    '2010': {
                        'name': 'Edinburgh East',
                        'post_id': '14419',
                    'mapit_url': 'http://mapit.mysociety.org/area/14419',
                    },
                    '2015': {
                        'name': 'Edinburgh North and Leith',
                        'post_id': '14420',
                        'mapit_url': 'http://mapit.mysociety.org/area/14420',
                        'elected': True,
                    },
                }
            }
        )

    def test_merge_standing_in_2015_null_in_primary(self):
        primary = {
            'standing_in': {
                '2010': {
                    'name': 'Edinburgh East',
                    'post_id': '14419',
                    'mapit_url': 'http://mapit.mysociety.org/area/14419',
                },
                '2015': None,
            }
        }
        secondary = {
            'standing_in': {
                '2010': {
                    'name': 'Aberdeen South',
                    'post_id': '14399',
                    'mapit_url': 'http://mapit.mysociety.org/area/14399',
                },
                '2015': {
                    'name': 'Aberdeen North',
                    'post_id': '14398',
                    'mapit_url': 'http://mapit.mysociety.org/area/14398',
                    'elected': False,
                },
            },
        }
        merged = merge_popit_people(primary, secondary)
        self.assertEqual(
            merged,
            {
                'standing_in': {
                    '2010': {
                        'name': 'Edinburgh East',
                        'post_id': '14419',
                        'mapit_url': 'http://mapit.mysociety.org/area/14419',
                    },
                    '2015': {
                        'name': 'Aberdeen North',
                        'post_id': '14398',
                        'mapit_url': 'http://mapit.mysociety.org/area/14398',
                        'elected': False,
                    },
                }
            }
        )

    def test_merge_standing_in_2015_null_in_secondary(self):
        primary = {
            'standing_in': {
                '2010': {
                    'name': 'Edinburgh East',
                    'post_id': '14419',
                    'mapit_url': 'http://mapit.mysociety.org/area/14419',
                },
                '2015': {
                    'name': 'Edinburgh North and Leith',
                    'post_id': '14420',
                    'mapit_url': 'http://mapit.mysociety.org/area/14420',
                },
            }
        }
        secondary = {
            'standing_in': {
                '2010': {
                    'name': 'Aberdeen South',
                    'post_id': '14399',
                    'mapit_url': 'http://mapit.mysociety.org/area/14399',
                },
                '2015': None
            },
        }
        merged = merge_popit_people(primary, secondary)
        self.assertEqual(
            merged,
            {
                'standing_in': {
                    '2010': {
                        'name': 'Edinburgh East',
                        'post_id': '14419',
                        'mapit_url': 'http://mapit.mysociety.org/area/14419',
                    },
                    '2015': {
                        'name': 'Edinburgh North and Leith',
                        'post_id': '14420',
                        'mapit_url': 'http://mapit.mysociety.org/area/14420',
                    },
                }
            }
        )

    def test_merge_conflicting_names(self):
        primary = {
            'name': 'Dave Cameron',
        }
        secondary = {
            'name': 'David Cameron',
        }
        merged = merge_popit_people(primary, secondary)
        self.assertEqual(
            merged,
            {
                'name': 'Dave Cameron',
                'other_names': [
                    {'name': 'David Cameron'}
                ]
            }
        )

    def test_fuller_merge_example(self):
        primary = {
            "name": "Julian Huppert",
            "other_names": [
                {
                    "end_date": None,
                    "id": "54b3fadc1f10dde30b97b3c4",
                    "name": "Julian Leon Huppert",
                    "note": "His full name, including the middle name ",
                    "start_date": None
                }
            ],
            "party_ppc_page_url": "http://www.libdems.org.uk/julian_huppert",
            "proxy_image": "http://candidates-posts.127.0.0.1.xip.io:3000/image-proxy//http%3A%2F%2Fyournextmp.popit.mysociety.org%2Fpersons%2F47%2Fimage%2F5481e8e0b150e238702c060d",
            "twitter_username": "JulianHuppert",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Julian_Huppert"
        }
        secondary = {
            "name": "Julian Huppert As Well",
            "other_names": [],
            "party_ppc_page_url": "",
            "proxy_image": None,
            "twitter_username": "",
            "wikipedia_url": ""
        }
        expected_result = {
            "name": "Julian Huppert",
            "other_names": [
                {
                    "end_date": None,
                    "id": "54b3fadc1f10dde30b97b3c4",
                    "name": "Julian Leon Huppert",
                    "note": "His full name, including the middle name ",
                    "start_date": None
                },
                {
                    'name': 'Julian Huppert As Well',
                },
            ],
            "party_ppc_page_url": "http://www.libdems.org.uk/julian_huppert",
            "proxy_image": "http://candidates-posts.127.0.0.1.xip.io:3000/image-proxy//http%3A%2F%2Fyournextmp.popit.mysociety.org%2Fpersons%2F47%2Fimage%2F5481e8e0b150e238702c060d",
            "twitter_username": "JulianHuppert",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Julian_Huppert"
        }
        merged = merge_popit_people(primary, secondary)
        self.assertEqual(
            merged,
            expected_result
        )

    def test_merge_conflicting_names_previous_other_names(self):
        primary = {
            'name': 'Dave Cameron',
            'other_names': [
                {'name': 'David W D Cameron'}
            ]
        }
        secondary = {
            'name': 'David Cameron',
            'other_names': [
                {'name': 'David William Donald Cameron'}
            ]
        }
        merged = merge_popit_people(primary, secondary)
        self.assertEqual(
            set(merged.keys()),
            set(['name', 'other_names'])
        )
        self.assertEqual(merged['name'], 'Dave Cameron')
        sorted_other_names = sorted(
            merged['other_names'],
            key=lambda e: e['name']
        )
        self.assertEqual(
            sorted_other_names,
            [
                {'name': 'David Cameron'},
                {'name': 'David W D Cameron'},
                {'name': 'David William Donald Cameron'},
            ],
        )

    def test_merge_versions(self):
        primary = {
            'name': 'Dave Cameron',
            'versions': [
                {
                    "version_id": "12fdb2d20e9e0753",
                    "information_source": "Some random update",
                },
                {
                    "version_id": "3570e9e02d2bdf21",
                    "information_source": "Original import",
                },
            ]
        }
        secondary = {
            'name': 'David Cameron',
            'versions': [
                {
                    "version_id": "b6fafb50a424b012",
                    "information_source": "Creation of a duplicate",
                },
            ]
        }
        merged = merge_popit_people(primary, secondary)
        self.assertEqual(
            merged,
            {
                'name': 'Dave Cameron',
                'other_names': [
                    {'name': 'David Cameron'}
                ],
                'versions': [
                    {
                        "version_id": "12fdb2d20e9e0753",
                        "information_source": "Some random update",
                    },
                    {
                        "version_id": "3570e9e02d2bdf21",
                        "information_source": "Original import",
                    },
                    {
                        "version_id": "b6fafb50a424b012",
                        "information_source": "Creation of a duplicate",
                    },
                ]
            }
        )

    def test_regression_merge_losing_memberships(self):
        # Stuart Jeffery has had various IDs:
        #    2111 (the current, canonical ID, originally created on 21st of December 2014)
        #    4850 (a later one, created on 13th of December 2014)
        #    12207 (latest, created on 13th April 2017)
        #
        # Two merges were done:
        #
        #    4850 (secondary) was merged into 2111 (primary) on 25th January 2015
        #    12207 (secondary) was merged into 2111 (primary) on 1st May 2016
        #
        # The first merge appeared to work fine, but the second lost
        # the 2010 and 2015 candidacies. That's the one we want to
        # reproduce, so we need the last version with ID 12207 as the
        # secondary. That is:
        secondary = {
            "birth_date": "",
            "email": "",
            "facebook_page_url": "",
            "facebook_personal_url": "",
            "gender": "",
            "homepage_url": "",
            "honorific_prefix": "",
            "honorific_suffix": "",
            "id": "12207",
            "image": None,
            "linkedin_url": "",
            "name": "Stuart Robert Jeffery",
            "other_names": [],
            "party_memberships": {
                "local.maidstone.2016-05-05": {
                    "id": "party:63",
                    "name": "Green Party"
                }
            },
            "party_ppc_page_url": "",
            "standing_in": {
                "local.maidstone.2016-05-05": {
                    "elected": False,
                    "name": "Shepway South ward",
                    "post_id": "DIW:E05005004"
                }
            },
            "twitter_username": "",
            "wikipedia_url": "",
        }
        # And the primary is the last version with ID 2111 before the merge:
        primary = {
            "birth_date": "1967-12-22",
            "email": "sjeffery@fmail.co.uk",
            "facebook_page_url": "",
            "facebook_personal_url": "",
            "gender": "male",
            "homepage_url": "http://www.stuartjeffery.net/",
            "honorific_prefix": "",
            "honorific_suffix": "",
            "id": "2111",
            "identifiers": [
                {
                    "identifier": "2111",
                    "scheme": "popit-person"
                },
                {
                    "identifier": "3476",
                    "scheme": "yournextmp-candidate"
                },
                {
                    "identifier": "15712527",
                    "scheme": "twitter"
                }
            ],
            "image": "http://yournextmp.popit.mysociety.org/persons/2111/image/54bc790ecb19ebca71e2af8e",
            "linkedin_url": "",
            "name": "Stuart Jeffery",
            "other_names": [],
            "party_memberships": {
                "2010": {
                    "id": "party:63",
                    "name": "Green Party"
                },
                "2015": {
                    "id": "party:63",
                    "name": "Green Party"
                }
            },
            "party_ppc_page_url": "https://my.greenparty.org.uk/candidates/105873",
            "standing_in": {
                "2010": {
                    "name": "Maidstone and The Weald",
                    "post_id": "65936"
                },
                "2015": {
                    "elected": False,
                    "name": "Canterbury",
                    "post_id": "65878"
                }
            },
            "twitter_username": "stuartjeffery",
            "wikipedia_url": ""
        }
        # What we observed from was that this merge lost the 2010 and
        # 2015 memberships.
        merged = merge_popit_people(primary, secondary)
        self.assertEqual(
            merged,
            {'birth_date': '1967-12-22',
             'email': 'sjeffery@fmail.co.uk',
             'facebook_page_url': '',
             'facebook_personal_url': '',
             'gender': 'male',
             'homepage_url': 'http://www.stuartjeffery.net/',
             'honorific_prefix': '',
             'honorific_suffix': '',
             'id': '2111',
             'identifiers': [{'identifier': '2111', 'scheme': 'popit-person'},
                              {'identifier': '3476',
                               'scheme': 'yournextmp-candidate'},
                              {'identifier': '15712527', 'scheme': 'twitter'}],
             'image': 'http://yournextmp.popit.mysociety.org/persons/2111/image/54bc790ecb19ebca71e2af8e',
             'linkedin_url': '',
             'name': 'Stuart Jeffery',
             'other_names': [{'name': 'Stuart Robert Jeffery'}],
             'party_memberships': {'2010': {'id': 'party:63',
                                              'name': 'Green Party'},
                                    '2015': {'id': 'party:63',
                                              'name': 'Green Party'},
                                    'local.maidstone.2016-05-05': {'id': 'party:63',
                                                                    'name': 'Green Party'}},
             'party_ppc_page_url': 'https://my.greenparty.org.uk/candidates/105873',
             'standing_in': {'2010': {'name': 'Maidstone and The Weald',
                                        'post_id': '65936'},
                              '2015': {'elected': False,
                                        'name': 'Canterbury',
                                        'post_id': '65878'},
                              'local.maidstone.2016-05-05': {'elected': False,
                                                              'name': 'Shepway South ward',
                                                              'post_id': 'DIW:E05005004'}},
             'twitter_username': 'stuartjeffery',
             'wikipedia_url': ''}
        )
