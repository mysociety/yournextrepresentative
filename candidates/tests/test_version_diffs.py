from __future__ import unicode_literals

import re

from django.test import TestCase

from candidates.diffs import get_version_diffs
from . import factories
from .uk_examples import UK2015ExamplesMixin


def sort_operations_for_comparison(versions_with_diffs):
    for v in versions_with_diffs:
        v['diffs'].sort(key=lambda pd: pd['parent_version_id'])
        for parent_data in v['diffs']:
            parent_data['parent_diff'].sort(key=lambda o: (o['op'], o['path']))


def tidy_html_whitespace(html):
    tidied = re.sub(r'(?ms)>\s+<', '><', html.strip())
    return re.sub(r'(?ms)\s+', ' ', tidied)


class TestVersionDiffs(UK2015ExamplesMixin, TestCase):

    maxDiff = None

    def setUp(self):
        super(TestVersionDiffs, self).setUp()

    def test_get_version_diffs(self):
        versions = [
            {
                'user': 'john',
                'information_source': 'Manual correction by a user',
                'timestamp': '2015-06-10T05:35:15.297559',
                'version_id': '8aa71db8f2f20bf8',
                'data': {
                    'id': '24680',
                    'a': 'alpha',
                    'b': 'beta',
                    'g': '',
                    'h': None,
                    'l': 'lambda',
                }
            },
            {
                'information_source': 'Updated by a script',
                'timestamp': '2015-05-08T01:52:27.061038',
                'version_id': '643dc3343880f168',
                'data': {
                    'id': '24680',
                    'a': 'alpha',
                    'b': 'LATIN SMALL LETTER B',
                    'd': 'delta',
                    'g': None,
                    'h': '',
                    'l': 'lambda',
                }
            },
            {
                'information_source': 'Original imported data',
                'timestamp': '2015-03-07T05:35:15.297559',
                'version_id': '42648e36ff699179',
                'data': {
                    'id': '24680',
                    'a': 'alpha',
                    'b': 'beta',
                    'l': None,
                }
            },
        ]

        expected_result = [
            {
                'user': 'john',
                'information_source': 'Manual correction by a user',
                'timestamp': '2015-06-10T05:35:15.297559',
                'version_id': '8aa71db8f2f20bf8',
                'parent_version_ids': ['643dc3343880f168'],
                'data': {
                    'id': '24680',
                    'a': 'alpha',
                    'b': 'beta',
                    'g': '',
                    'h': None,
                    'l': 'lambda',
                },
                'diffs': [
                    {
                        'parent_version_id': '643dc3343880f168',
                        'parent_diff': [
                            {
                                'op': 'remove',
                                'path': 'd',
                                'previous_value': 'delta',
                            },
                            {
                                'op': 'replace',
                                'path': 'b',
                                'previous_value': 'LATIN SMALL LETTER B',
                                'value': 'beta',
                            }
                        ]
                    }
                ]
            },
            {
                'information_source': 'Updated by a script',
                'timestamp': '2015-05-08T01:52:27.061038',
                'version_id': '643dc3343880f168',
                'parent_version_ids': ['42648e36ff699179'],
                'data': {
                    'id': '24680',
                    'a': 'alpha',
                    'b': 'LATIN SMALL LETTER B',
                    'd': 'delta',
                    'g': None,
                    'h': '',
                    'l': 'lambda',
                },
                'diffs': [
                    {
                        'parent_version_id': '42648e36ff699179',
                        'parent_diff': [
                            {
                                'op': 'add',
                                'path': 'd',
                                'value': 'delta',
                            },
                            {
                                'op': 'add',
                                'path': 'l',
                                'previous_value': None,
                                'value': 'lambda',
                            },
                            {
                                'op': 'replace',
                                'path': 'b',
                                'previous_value': 'beta',
                                'value': 'LATIN SMALL LETTER B',
                            },
                        ]
                    }
                ]
            },
            {
                'information_source': 'Original imported data',
                'timestamp': '2015-03-07T05:35:15.297559',
                'version_id': '42648e36ff699179',
                'parent_version_ids': [],
                'data': {
                    'id': '24680',
                    'a': 'alpha',
                    'b': 'beta',
                    'l': None,
                },
                'diffs': [
                    {
                        'parent_version_id': None,
                        'parent_diff': [
                            {
                                'op': 'add',
                                'path': 'a',
                                'value': 'alpha',
                            },
                            {
                                'op': 'add',
                                'path': 'b',
                                'value': 'beta',
                            },
                            {
                                'op': 'add',
                                'path': 'id',
                                'value': '24680',
                            },
                        ]
                    }
                ],
            },
        ]

        versions_with_diffs = get_version_diffs(versions)
        sort_operations_for_comparison(versions_with_diffs)

        self.assertEqual(expected_result, versions_with_diffs)

    def test_versions_2010_then_adding_2015(self):
        versions = [
            {
                'information_source': 'After clicking "Standing again"',
                'timestamp': '2015-05-08T01:52:27.061038',
                'version_id': '3aa8d7da968e10fa',
                'data': {
                    'id': '24680',
                    'standing_in': {
                        '2010': {
                            'name': 'South Cambridgeshire',
                            'post_id': '65922',
                            'mapit_url': 'http://mapit.mysociety.org/area/65922',
                        },
                        '2015': {
                            'name': 'Edinburgh North and Leith',
                            'post_id': '14420',
                            'mapit_url': 'http://mapit.mysociety.org/area/14420',
                        },
                    }
                }
            },
            {
                'information_source': 'Original imported data',
                'timestamp': '2015-03-10T05:35:15.297559',
                'version_id': 'fd105d1cf3b5ed0f',
                'data': {
                    'id': '24680',
                    'standing_in': {
                        '2010': {
                            'name': 'South Cambridgeshire',
                            'post_id': '65922',
                            'mapit_url': 'http://mapit.mysociety.org/area/65922',
                        },
                    }
                }
            },
        ]

        expected_result = [
            {
                'information_source': 'After clicking "Standing again"',
                'timestamp': '2015-05-08T01:52:27.061038',
                'version_id': '3aa8d7da968e10fa',
                'parent_version_ids': ['fd105d1cf3b5ed0f'],
                'data': {
                    'id': '24680',
                    'standing_in': {
                        '2010': {
                            'name': 'South Cambridgeshire',
                            'post_id': '65922',
                        },
                        '2015': {
                            'name': 'Edinburgh North and Leith',
                            'post_id': '14420',
                        },
                    }
                },
                'diffs': [
                    {
                        'parent_version_id': 'fd105d1cf3b5ed0f',
                        'parent_diff': [
                            {
                                'op': 'add',
                                'path': 'standing_in/2015',
                                'value': 'is known to be standing in Edinburgh North and Leith in the 2015 General Election',
                            }
                        ]
                    }
                ]
            },
            {
                'information_source': 'Original imported data',
                'timestamp': '2015-03-10T05:35:15.297559',
                'version_id': 'fd105d1cf3b5ed0f',
                'parent_version_ids': [],
                'data': {
                    'id': '24680',
                    'standing_in': {
                        '2010': {
                            'name': 'South Cambridgeshire',
                            'post_id': '65922',
                        },
                    }
                },
                'diffs': [
                    {
                        'parent_version_id': None,
                        'parent_diff': [
                            {
                                'op': 'add',
                                'path': 'id',
                                'value': '24680',

                            },
                            {
                                'op': 'add',
                                'path': 'standing_in',
                                'value': 'was known to be standing in South Cambridgeshire in the 2010 General Election',
                            },
                        ]
                    }
                ]
            },
        ]

        versions_with_diffs = get_version_diffs(versions)
        sort_operations_for_comparison(versions_with_diffs)

        self.assertEqual(expected_result, versions_with_diffs)

    def test_versions_2010_then_definitely_not_2015(self):
        versions = [
            {
                'information_source': 'After clicking "Not standing again"',
                'timestamp': '2015-05-08T01:52:27.061038',
                'version_id': '698ae05960970b60',
                'data': {
                    'id': '24680',
                    'standing_in': {
                        '2010': {
                            'name': 'South Cambridgeshire',
                            'post_id': '65922',
                            'mapit_url': 'http://mapit.mysociety.org/area/65922',
                        },
                        '2015': None,
                    }
                }
            },
            {
                'information_source': 'Original imported data',
                'timestamp': '2015-03-10T05:35:15.297559',
                'version_id': 'd1fd9c3830d8d722',
                'data': {
                    'id': '24680',
                    'standing_in': {
                        '2010': {
                            'name': 'South Cambridgeshire',
                            'post_id': '65922',
                            'mapit_url': 'http://mapit.mysociety.org/area/65922',
                        },
                    }
                }
            },
        ]

        expected_result = [
            {
                'information_source': 'After clicking "Not standing again"',
                'timestamp': '2015-05-08T01:52:27.061038',
                'version_id': '698ae05960970b60',
                'parent_version_ids': ['d1fd9c3830d8d722'],
                'data': {
                    'id': '24680',
                    'standing_in': {
                        '2010': {
                            'name': 'South Cambridgeshire',
                            'post_id': '65922',
                        },
                        '2015': None,
                    }
                },
                'diffs': [
                    {
                        'parent_version_id': 'd1fd9c3830d8d722',
                        'parent_diff': [
                            {
                                'op': 'add',
                                'path': 'standing_in/2015',
                                'value': 'is known not to be standing in the 2015 General Election',
                            }
                        ]
                    }
                ],
            },
            {
                'information_source': 'Original imported data',
                'timestamp': '2015-03-10T05:35:15.297559',
                'version_id': 'd1fd9c3830d8d722',
                'parent_version_ids': [],
                'data': {
                    'id': '24680',
                    'standing_in': {
                        '2010': {
                            'name': 'South Cambridgeshire',
                            'post_id': '65922',
                        },
                    }
                },
                'diffs': [
                    {
                        'parent_version_id': None,
                        'parent_diff': [
                            {
                                'op': 'add',
                                'path': 'id',
                                'value': '24680',
                            },
                            {
                                'op': 'add',
                                'path': 'standing_in',
                                'value': 'was known to be standing in South Cambridgeshire in the 2010 General Election',
                            }
                        ]
                    }
                ]
            },
        ]

        versions_with_diffs = get_version_diffs(versions)
        sort_operations_for_comparison(versions_with_diffs)

        self.assertEqual(expected_result, versions_with_diffs)

    def test_versions_just_party_changed(self):
        versions = [
            {
                'information_source': 'After clicking "Not standing again"',
                'timestamp': '2015-05-08T01:52:27.061038',
                'version_id': '95ac9c97c1d72ebb',
                'data': {
                    'id': '24680',
                    'party_memberships': {
                        '2010': {
                            'id': 'party:58',
                            'name': 'Mebyon Kernow - The Party for Cornwall'
                        },
                        '2015': {
                            'id': 'ynmp-party:2',
                            'name': 'Independent'
                        }
                    },
                }
            },
            {
                'information_source': 'Original imported data',
                'timestamp': '2015-03-10T05:35:15.297559',
                'version_id': '10fcaee60b9f5203',
                'data': {
                    'id': '24680',
                    'party_memberships': {
                        '2010': {
                            'id': 'party:58',
                            'name': 'Mebyon Kernow - The Party for Cornwall'
                        },
                        '2015': {
                            'id': 'party:58',
                            'name': 'Mebyon Kernow - The Party for Cornwall'
                        }
                    },
                }
            },
        ]

        expected_result = [
            {
                'information_source': 'After clicking "Not standing again"',
                'timestamp': '2015-05-08T01:52:27.061038',
                'version_id': '95ac9c97c1d72ebb',
                'parent_version_ids': ['10fcaee60b9f5203'],
                'data': {
                    'id': '24680',
                    'party_memberships': {
                        '2010': {
                            'id': 'party:58',
                            'name': 'Mebyon Kernow - The Party for Cornwall'
                        },
                        '2015': {
                            'id': 'ynmp-party:2',
                            'name': 'Independent'
                        }
                    },
                },
                'diffs': [
                    {
                        'parent_version_id': '10fcaee60b9f5203',
                        'parent_diff':  [
                            {
                                'op': 'replace',
                                'path': 'party_memberships/2015/id',
                                'previous_value': 'is known to be standing for the party with ID party:58 in the 2015 General Election',
                                'value': 'is known to be standing for the party with ID ynmp-party:2 in the 2015 General Election',
                            },
                            {
                                'op': 'replace',
                                'path': 'party_memberships/2015/name',
                                'previous_value': 'is known to be standing for the party \'Mebyon Kernow - The Party for Cornwall\' in the 2015 General Election',
                                'value': 'is known to be standing for the party \'Independent\' in the 2015 General Election',
                            },
                        ],
                    }
                ]
            },
            {
                'information_source': 'Original imported data',
                'timestamp': '2015-03-10T05:35:15.297559',
                'version_id': '10fcaee60b9f5203',
                'parent_version_ids': [],
                'data': {
                    'id': '24680',
                    'party_memberships': {
                        '2010': {
                            'id': 'party:58',
                            'name': 'Mebyon Kernow - The Party for Cornwall'
                        },
                        '2015': {
                            'id': 'party:58',
                            'name': 'Mebyon Kernow - The Party for Cornwall'
                        }
                    },
                },
                'diffs': [
                    {
                        'parent_version_id': None,
                        'parent_diff': [
                            {
                                'op': 'add',
                                'path': 'id',
                                'value': '24680',
                            },
                            {
                                'op': 'add',
                                'path': 'party_memberships',
                                'value': 'is known to be standing for the party "Mebyon Kernow - The Party for Cornwall" in the 2015 General Election and was known to be standing for the party "Mebyon Kernow - The Party for Cornwall" in the 2010 General Election',
                            },
                        ]
                    }
                ]
            },
        ]

        versions_with_diffs = get_version_diffs(versions)
        sort_operations_for_comparison(versions_with_diffs)

        self.assertEqual(expected_result, versions_with_diffs)

    def test_versions_just_constituency_changed(self):
        versions = [
            {
                'information_source': 'After clicking "Not standing again"',
                'timestamp': '2015-05-08T01:52:27.061038',
                'version_id': '65c16b93a0f41b00',
                'data': {
                    'id': '24680',
                    'standing_in': {
                        '2015': {'mapit_url': 'http://mapit.mysociety.org/area/65659',
                                 'name': 'Truro and Falmouth',
                                 'post_id': '65659'}
                    },
                }
            },
            {
                'information_source': 'Original imported data',
                'timestamp': '2015-03-10T05:35:15.297559',
                'version_id': '1a5144605b4c1498',
                'data': {
                    'id': '24680',
                    "standing_in": {
                        "2015": {
                            "post_id": "65808",
                            "name": "Dulwich and West Norwood",
                            "mapit_url": "http://mapit.mysociety.org/area/65808"
                        },
                    },
                }
            },
        ]

        expected_result = [
            {
                'information_source': 'After clicking "Not standing again"',
                'timestamp': '2015-05-08T01:52:27.061038',
                'version_id': '65c16b93a0f41b00',
                'parent_version_ids': ['1a5144605b4c1498'],
                'data': {
                    'id': '24680',
                    'standing_in': {
                        '2015': {'name': 'Truro and Falmouth',
                                 'post_id': '65659'}
                    },
                },
                'diffs': [
                    {
                        'parent_version_id': '1a5144605b4c1498',
                        'parent_diff': [
                            {
                                'op': 'replace',
                                'path': 'standing_in/2015/name',
                                'previous_value': 'is known to be standing in Dulwich and West Norwood in the 2015 General Election',
                                'value': 'is known to be standing in Truro and Falmouth in the 2015 General Election',
                            },
                            {
                                'op': 'replace',
                                'path': 'standing_in/2015/post_id',
                                'previous_value': 'is known to be standing for the post with ID 65808 in the 2015 General Election',
                                'value': 'is known to be standing for the post with ID 65659 in the 2015 General Election',
                            },
                        ]
                    }
                ]
            },
            {
                'information_source': 'Original imported data',
                'timestamp': '2015-03-10T05:35:15.297559',
                'version_id': '1a5144605b4c1498',
                'parent_version_ids': [],
                'data': {
                    'id': '24680',
                    "standing_in": {
                        "2015": {
                            "post_id": "65808",
                            "name": "Dulwich and West Norwood",
                        },
                    },
                },
                'diffs': [
                    {
                        'parent_version_id': None,
                        'parent_diff': [
                            {
                                'op': 'add',
                                'path': 'id',
                                'value': '24680',
                            },
                            {
                                'op': 'add',
                                'path': 'standing_in',
                                'value': 'is known to be standing in Dulwich and West Norwood in the 2015 General Election',
                            },
                        ]
                    }
                ]
            },
        ]

        versions_with_diffs = get_version_diffs(versions)
        sort_operations_for_comparison(versions_with_diffs)

        self.assertEqual(expected_result, versions_with_diffs)

    def test_remove_ids_for_version_diffs(self):
        versions = [
            {
                'user': 'john',
                'information_source': 'Manual correction by a user',
                'timestamp': '2015-04-12T05:35:15.297559',
                'version_id': 'e6dcd55bb903499e',
                'data': {
                    'id': '24680',
                    'identifiers': [
                        {
                            'scheme': 'yournextmp-candidate',
                            'identifier': '2009',
                            'id': '123456',
                        },
                    ],
                    'other_names': [
                        {
                            'note': 'Full name',
                            'start_date': None,
                            'id': '567890',
                            'end_date': None,
                            'name': 'Tessa Jane Jowell'
                        }
                    ]
                }
            },
            {
                'information_source': 'Updated by a script',
                'timestamp': '2015-03-10T05:35:15.297559',
                'version_id': '788a3291f1103de5',
                'data': {
                    'id': '24680',
                    'identifiers': [
                        {
                            'scheme': 'yournextmp-candidate',
                            'identifier': '2009',
                            'id': '123457',
                        }
                    ],
                    'other_names': [
                        {
                            'note': 'Full name',
                            'start_date': None,
                            'id': '567891',
                            'end_date': None,
                            'name': 'Tessa J Jowell'
                        }
                    ]
                }
            },
        ]

        expected_result = [
            {
                'user': 'john',
                'information_source': 'Manual correction by a user',
                'timestamp': '2015-04-12T05:35:15.297559',
                'version_id': 'e6dcd55bb903499e',
                'parent_version_ids': ['788a3291f1103de5'],
                'data': {
                    'id': '24680',
                    'identifiers': [
                        {
                            'scheme': 'yournextmp-candidate',
                            'identifier': '2009',
                        },
                    ],
                    'other_names': [
                        {
                            'note': 'Full name',
                            'start_date': None,
                            'end_date': None,
                            'name': 'Tessa Jane Jowell'
                        }
                    ],
                },
                'diffs': [
                    {
                        'parent_version_id': '788a3291f1103de5',
                        'parent_diff': [
                            {
                                'path': 'other_names/0/name',
                                'previous_value': 'Tessa J Jowell',
                                'value': 'Tessa Jane Jowell',
                                'op': 'replace'
                            }
                        ]
                    }
                ],
            },
            {
                'information_source': 'Updated by a script',
                'timestamp': '2015-03-10T05:35:15.297559',
                'version_id': '788a3291f1103de5',
                'parent_version_ids': [],
                'data': {
                    'id': '24680',
                    'identifiers': [
                        {
                            'scheme': 'yournextmp-candidate',
                            'identifier': '2009',
                        },
                    ],
                    'other_names': [
                        {
                            'note': 'Full name',
                            'start_date': None,
                            'end_date': None,
                            'name': 'Tessa J Jowell'
                        }
                    ]
                },
                'diffs': [
                    {
                        'parent_version_id': None,
                        'parent_diff': [
                            {
                                'op': 'add',
                                'path': 'id',
                                'value': '24680',
                            },
                            {
                                "op": "add",
                                "path": "identifiers",
                                "value": [
                                    {
                                        "identifier": "2009",
                                        "scheme": "yournextmp-candidate"
                                    }
                                ]
                            },
                            {
                                "op": "add",
                                "path": "other_names",
                                "value": [
                                    {
                                        "end_date": None,
                                        "name": "Tessa J Jowell",
                                        "note": "Full name",
                                        "start_date": None
                                    }
                                ]
                            }
                        ],
                    }
                ],
            },
        ]

        versions_with_diffs = get_version_diffs(versions)
        sort_operations_for_comparison(versions_with_diffs)

        self.assertEqual(expected_result, versions_with_diffs)

    def test_index_error(self):
        versions = [
            {
                'user': 'john',
                'information_source': 'Manual correction by a user',
                'timestamp': '2015-04-12T05:35:15.297559',
                'version_id': 'a2fd462d7b9ea219',
                'data': {
                    'id': '24680',
                    'identifiers': [
                        {
                            'scheme': 'yournextmp-candidate',
                            'identifier': '2009',
                            'id': '123456',
                        },
                    ],
                    'other_names': [
                        {
                            'end_date': '',
                            'name': 'Joey',
                            'note': '',
                            'start_date': ''
                        },
                        {
                            'end_date': '',
                            'name': 'Joseph Tribbiani',
                            'note': '',
                            'start_date': ''
                        },
                        {
                            'end_date': '',
                            'name': 'Jonathan Francis Tribbiani',
                            'note': 'Ballot paper',
                            'start_date': ''
                        }
                    ]
                }
            },
            {
                'information_source': 'Updated by a script',
                'timestamp': '2015-03-10T05:35:15.297559',
                'version_id': '66b78855c5f19197',
                'data': {
                    'id': '24680',
                    'identifiers': [
                        {
                            'scheme': 'yournextmp-candidate',
                            'identifier': '2009',
                            'id': '123457',
                        }
                    ],
                    'other_names': [
                        {
                            'end_date': '',
                            'name': 'Joseph Tribbiani',
                            'note': '',
                            'start_date': ''
                        },
                        {
                            'end_date': '',
                            'name': 'Jonathan Francis Tribbiani',
                            'note': 'Ballot paper',
                            'start_date': ''
                        },
                        {
                            'end_date': '',
                            'name': 'Joey',
                            'note': '',
                            'start_date': ''
                        }
                    ]
                }
            },
        ]

        expected_result = [
            {
                'information_source': 'Manual correction by a user',
                'timestamp': '2015-04-12T05:35:15.297559',
                'version_id': 'a2fd462d7b9ea219',
                'parent_version_ids': ['66b78855c5f19197'],
                'diffs': [
                    {
                        'parent_version_id': '66b78855c5f19197',
                        'parent_diff': [
                            {
                                'path': 'other_names/0',
                                'value': {
                                    'note': '',
                                    'name': 'Joey',
                                    'end_date': '',
                                    'start_date': ''
                                },
                                'op': 'add'
                            },
                            {
                                'path': 'other_names/3',
                                'previous_value': {
                                    'note': '',
                                    'name': 'Joey',
                                    'end_date': '',
                                    'start_date': ''
                                },
                                'op': 'remove'
                            }
                        ]
                    }
                ],
                'data': {
                    'id': '24680',
                    'identifiers': [
                        {
                            'scheme': 'yournextmp-candidate',
                            'identifier': '2009'
                        }
                    ],
                    'other_names': [
                        {
                            'note': '',
                            'name': 'Joey',
                            'end_date': '',
                            'start_date': ''
                        },
                        {
                            'note': '',
                            'name': 'Joseph Tribbiani',
                            'end_date': '', 'start_date': ''
                        },
                        {
                            'note': 'Ballot paper',
                            'name': 'Jonathan Francis Tribbiani',
                            'end_date': '',
                            'start_date': ''
                        }
                    ]
                },
                'user': 'john'
            },
            {
                'information_source': 'Updated by a script',
                'timestamp': '2015-03-10T05:35:15.297559',
                'version_id': '66b78855c5f19197',
                'parent_version_ids': [],
                'diffs': [
                    {
                        'parent_version_id': None,
                        'parent_diff': [
                            {
                                'path': 'identifiers',
                                'value': [
                                    {
                                        'scheme': 'yournextmp-candidate',
                                        'identifier': '2009'
                                    }
                                ],
                                'op': 'add'
                            },
                            {
                                'path': 'other_names',
                                'value': [
                                    {
                                        'note': '',
                                        'name': 'Joseph Tribbiani',
                                        'end_date': '',
                                        'start_date': ''
                                    },
                                    {
                                        'note': 'Ballot paper',
                                        'name': 'Jonathan Francis Tribbiani',
                                        'end_date': '',
                                        'start_date': ''
                                    },
                                    {
                                        'note': '',
                                        'name': 'Joey',
                                        'end_date': '',
                                        'start_date': ''
                                    }
                                ],
                                'op': 'add'
                            }
                        ],
                    }
                ],
                'data': {
                    'id': '24680',
                    'identifiers': [
                        {
                            'scheme': 'yournextmp-candidate',
                            'identifier': '2009'
                        }
                    ],
                    'other_names': [
                        {
                            'note': '',
                            'name': 'Joseph Tribbiani',
                            'end_date': '',
                            'start_date': ''
                        },
                        {
                            'note': 'Ballot paper',
                            'name': 'Jonathan Francis Tribbiani',
                            'end_date': '',
                            'start_date': ''
                        },
                        {
                            'note': '',
                            'name': 'Joey',
                            'end_date': '',
                            'start_date': ''
                        }
                    ]
                }
            }
        ]

        # This shouldn't raise an exception, but does at the moment:
        versions_with_diffs = get_version_diffs(versions)
        sort_operations_for_comparison(versions_with_diffs)

        self.assertEqual(expected_result, versions_with_diffs)

    def test_index_error(self):
        versions = [
            {
                'user': 'john',
                'information_source': 'Manual correction by a user',
                'timestamp': '2015-05-08T01:52:27.061038',
                'version_id': '1d33caabf421c656',
                'data': {
                    'id': '24680',
                    'identifiers': [
                        {
                            'scheme': 'yournextmp-candidate',
                            'identifier': '2009',
                            'id': '123456',
                        },
                    ],
                    'other_names': [
                        {
                            'end_date': '',
                            'name': 'Joey',
                            'note': '',
                            'start_date': ''
                        },
                        {
                            'end_date': '',
                            'name': 'Joseph Tribbiani',
                            'note': '',
                            'start_date': ''
                        },
                        {
                            'end_date': '',
                            'name': 'Jonathan Francis Tribbiani',
                            'note': 'Ballot paper',
                            'start_date': ''
                        }
                    ]
                }
            },
            {
                'information_source': 'Updated by a script',
                'timestamp': '2015-03-10T05:35:15.297559',
                'version_id': 'f7cc564751d31a2b',
                'data': {
                    'id': '24680',
                    'identifiers': [
                        {
                            'scheme': 'yournextmp-candidate',
                            'identifier': '2009',
                            'id': '123457',
                        }
                    ],
                    'other_names': [
                        {
                            'end_date': '',
                            'name': 'Joseph Tribbiani',
                            'note': '',
                            'start_date': ''
                        },
                        {
                            'end_date': '',
                            'name': 'Jonathan Francis Tribbiani',
                            'note': 'Ballot paper',
                            'start_date': ''
                        },
                        {
                            'end_date': '',
                            'name': 'Joey',
                            'note': '',
                            'start_date': ''
                        }
                    ]
                }
            },
        ]

        expected_result = [
            {
                'information_source': 'Manual correction by a user',
                'timestamp': '2015-05-08T01:52:27.061038',
                'version_id': '1d33caabf421c656',
                'parent_version_ids': ['f7cc564751d31a2b'],
                'diffs': [
                    {
                        'parent_version_id': 'f7cc564751d31a2b',
                        'parent_diff': [
                            {
                                'path': 'other_names/0',
                                'value': {
                                    'note': '',
                                    'name': 'Joey',
                                    'end_date': '',
                                    'start_date': ''
                                },
                                'op': 'add'
                            },
                            {
                                'path': 'other_names/3',
                                'previous_value': {
                                    'note': '',
                                    'name': 'Joey',
                                    'end_date': '',
                                    'start_date': ''
                                },
                                'op': 'remove'
                            }
                        ]
                    }
                ],
                'data': {
                    'id': '24680',
                    'identifiers': [
                        {
                            'scheme': 'yournextmp-candidate',
                            'identifier': '2009'
                        }
                    ],
                    'other_names': [
                        {
                            'note': '',
                            'name': 'Joey',
                            'end_date': '',
                            'start_date': ''
                        },
                        {
                            'note': '',
                            'name': 'Joseph Tribbiani',
                            'end_date': '', 'start_date': ''
                        },
                        {
                            'note': 'Ballot paper',
                            'name': 'Jonathan Francis Tribbiani',
                            'end_date': '',
                            'start_date': ''
                        }
                    ]
                },
                'user': 'john'
            },
            {
                'information_source': 'Updated by a script',
                'timestamp': '2015-03-10T05:35:15.297559',
                'version_id': 'f7cc564751d31a2b',
                'parent_version_ids': [],
                'diffs': [
                    {
                        'parent_version_id': None,
                        'parent_diff': [
                            {
                                'op': 'add',
                                'path': 'id',
                                'value': '24680',
                            },
                            {
                                'path': 'identifiers',
                                'value': [
                                    {
                                        'scheme': 'yournextmp-candidate',
                                        'identifier': '2009'
                                    }
                                ],
                                'op': 'add'
                            },
                            {
                                'path': 'other_names',
                                'value': [
                                    {
                                        'note': '',
                                        'name': 'Joseph Tribbiani',
                                        'end_date': '',
                                        'start_date': ''
                                    },
                                    {
                                        'note': 'Ballot paper',
                                        'name': 'Jonathan Francis Tribbiani',
                                        'end_date': '',
                                        'start_date': ''
                                    },
                                    {
                                        'note': '',
                                        'name': 'Joey',
                                        'end_date': '',
                                        'start_date': ''
                                    }
                                ],
                                'op': 'add'
                            }
                        ],
                    }
                ],
                'data': {
                    'id': '24680',
                    'identifiers': [
                        {
                            'scheme': 'yournextmp-candidate',
                            'identifier': '2009'
                        }
                    ],
                    'other_names': [
                        {
                            'note': '',
                            'name': 'Joseph Tribbiani',
                            'end_date': '',
                            'start_date': ''
                        },
                        {
                            'note': 'Ballot paper',
                            'name': 'Jonathan Francis Tribbiani',
                            'end_date': '',
                            'start_date': ''
                        },
                        {
                            'note': '',
                            'name': 'Joey',
                            'end_date': '',
                            'start_date': ''
                        }
                    ]
                }
            }
        ]

        # This shouldn't raise an exception, but does at the moment:
        versions_with_diffs = get_version_diffs(versions)
        sort_operations_for_comparison(versions_with_diffs)

        self.assertEqual(expected_result, versions_with_diffs)


    def test_alternative_names(self):
        versions = [{
            'data': {
                'honorific_prefix': 'Mrs',
                'honorific_suffix': '',
                'id': '6704',
                'identifiers': [{'id': '552f80d0ed1c6ee164eeae51',
                'identifier': '13445',
                'scheme': 'yournextmp-candidate'}],
                'image': None,
                'linkedin_url': '',
                'name': 'Sarah Jones',
                'other_names': [{
                    'id': '552f80d0ed1c6ee164eeae50',
                    'name': 'Sarah Smith',
                    'note': 'Maiden name'
                }],
                'party_ppc_page_url': '',
                'proxy_image': None,
                'twitter_username': '',
                'wikipedia_url': ''
            },
            'information_source': 'Made up 2',
            'timestamp': '2015-05-08T01:52:27.061038',
            'username': 'test',
            'version_id': '3fc494d54f61a157'
        },

        {
            'data': {
                'honorific_prefix': 'Mrs',
                'honorific_suffix': '',
                'id': '6704',
                'identifiers': [{
                    'id': '5477866f737edc5252ce5938',
                    'identifier': '13445',
                    'scheme': 'yournextmp-candidate'
                }],
                'image': None,
                'linkedin_url': '',
                'name': 'Sarah Jones',
                'other_names': [
                    {'name': 'Sarah Smith'}
                ],
                'party_ppc_page_url': '',
                'proxy_image': None,
                'twitter_username': '',
                'wikipedia_url': ''
            },
            'information_source': 'Made up 1',
            'timestamp': '2015-03-10T05:35:15.297559',
            'username': 'test',
            'version_id': '2f07734529a83242'
        }]

        versions_with_diffs = get_version_diffs(versions)
        sort_operations_for_comparison(versions_with_diffs)
        expected_result = [{
            'information_source': 'Made up 2',
            'username': 'test',
            'timestamp': '2015-05-08T01:52:27.061038',
            'version_id': '3fc494d54f61a157',
            'parent_version_ids': ['2f07734529a83242'],
            'diffs': [
                {
                    'parent_version_id': '2f07734529a83242',
                    'parent_diff': [{
                        'path': 'other_names/0/note',
                        'previous_value': None,
                        'value': 'Maiden name',
                        'op': 'add'
                    }],
                }
            ],
            'data': {
                'honorific_suffix': '',
                'party_ppc_page_url': '',
                'linkedin_url': '',
                'image': None,
                'twitter_username': '',
                'id': '6704',
                'name': 'Sarah Jones',
                'identifiers': [{
                    'scheme': 'yournextmp-candidate',
                    'identifier': '13445'
                }],
                'other_names': [{
                    'note': 'Maiden name',
                    'name': 'Sarah Smith'
                }],
                'honorific_prefix': 'Mrs',
                'wikipedia_url': ''
            }
        },
        {
            'information_source': 'Made up 1',
            'username': 'test',
            'timestamp': '2015-03-10T05:35:15.297559',
            'version_id': '2f07734529a83242',
            'parent_version_ids': [],
            'diffs': [
                {
                    'parent_version_id': None,
                    'parent_diff': [
                        {
                            'path': 'honorific_prefix',
                            'value': 'Mrs',
                            'op': 'add'
                        },
                        {
                            'path': 'id',
                            'value': '6704',
                            'op': 'add'
                        },
                        {
                            'path': 'identifiers',
                            'value': [{
                                'scheme': 'yournextmp-candidate',
                                'identifier': '13445'
                            }],
                            'op': 'add'
                        },
                        {
                            'path': 'name',
                            'value': 'Sarah Jones',
                            'op': 'add'
                        },
                        {
                        'path': 'other_names',
                            'value': [{
                                'name': 'Sarah Smith'
                            }],
                            'op': 'add'
                        }
                    ],
                }
            ],
            'data': {
                'honorific_suffix': '',
                'party_ppc_page_url': '',
                'linkedin_url': '',
                'image': None,
                'twitter_username': '',
                'id': '6704',
                'name': 'Sarah Jones',
                'identifiers': [{'scheme': 'yournextmp-candidate',
                'identifier': '13445'}],
                'other_names': [{'name': 'Sarah Smith'}],
                'honorific_prefix': 'Mrs',
                'wikipedia_url': ''
            }
        }]
        self.assertEqual(expected_result, versions_with_diffs)

class TestSingleVersionRendering(UK2015ExamplesMixin, TestCase):

    maxDiff = None

    def setUp(self):
        super(TestSingleVersionRendering, self).setUp()
        self.example_person_extra = factories.PersonExtraFactory.create(
            base__name='Sarah Jones',
            versions='''[{
                "data": {
                    "honorific_prefix": "Mrs",
                    "honorific_suffix": "",
                    "id": "6704",
                    "identifiers": [{"id": "552f80d0ed1c6ee164eeae51",
                    "identifier": "13445",
                    "scheme": "yournextmp-candidate"}],
                    "image": null,
                    "linkedin_url": "",
                    "name": "Sarah Jones",
                    "other_names": [{
                        "id": "552f80d0ed1c6ee164eeae50",
                        "name": "Sarah Smith",
                        "note": "Maiden name"
                    }],
                    "party_ppc_page_url": "",
                    "proxy_image": null,
                    "twitter_username": "",
                    "wikipedia_url": ""
                },
                "information_source": "Made up 2",
                "timestamp": "2015-05-08T01:52:27.061038",
                "username": "test",
                "version_id": "3fc494d54f61a157"
            },
            {
                "data": {
                    "honorific_prefix": "Mrs",
                    "honorific_suffix": "",
                    "id": "6704",
                    "identifiers": [{
                        "id": "5477866f737edc5252ce5938",
                        "identifier": "13445",
                        "scheme": "yournextmp-candidate"
                    }],
                    "image": null,
                    "linkedin_url": "",
                    "name": "Sarah Jones",
                    "other_names": [
                        {"name": "Sarah Smith"}
                    ],
                    "party_ppc_page_url": "",
                    "proxy_image": null,
                    "twitter_username": "",
                    "wikipedia_url": ""
                },
                "information_source": "Made up 1",
                "timestamp": "2015-03-10T05:35:15.297559",
                "username": "test",
                "version_id": "2f07734529a83242"
            }]'''
        )

    def test_get_single_parent_diff(self):
        self.assertEqual(
            tidy_html_whitespace(
                self.example_person_extra.diff_for_version('3fc494d54f61a157')),
            '<dl>'
            '<dt>Changes made compared to parent 2f07734529a83242</dt>'
            '<dd><p class="version-diff"><span class="version-op-add">Added: other_names/0/note =&gt; &quot;Maiden name&quot;</span><br/></p></dd>'
            '</dl>')

    def test_get_zero_parent_diff(self):
        self.assertEqual(
            tidy_html_whitespace(
                self.example_person_extra.diff_for_version('2f07734529a83242')),
            '''<dl><dt>Changes made in initial version</dt><dd><p class="version-diff"><span class="version-op-add">Added: honorific_prefix =&gt; &quot;Mrs&quot;</span><br/><span class="version-op-add">Added: id =&gt; &quot;6704&quot;</span><br/><span class="version-op-add">Added: identifiers =&gt; [ { &quot;identifier&quot;: &quot;13445&quot;, &quot;scheme&quot;: &quot;yournextmp-candidate&quot; } ]</span><br/><span class="version-op-add">Added: name =&gt; &quot;Sarah Jones&quot;</span><br/><span class="version-op-add">Added: other_names =&gt; [ { &quot;name&quot;: &quot;Sarah Smith&quot; } ]</span><br/></p></dd></dl>''')

    def test_include_inline_style_colouring(self):
        self.assertEqual(
            tidy_html_whitespace(
                self.example_person_extra.diff_for_version(
                    '3fc494d54f61a157', inline_style=True)),
            '<dl>'
            '<dt>Changes made compared to parent 2f07734529a83242</dt>'
            '<dd><p class="version-diff"><span class="version-op-add" style="color: #0a6b0c">Added: other_names/0/note =&gt; &quot;Maiden name&quot;</span><br/></p></dd>'
            '</dl>')
