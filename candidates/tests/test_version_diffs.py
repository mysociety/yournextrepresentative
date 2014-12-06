from django.test import TestCase

from ..diffs import get_version_diffs

class TestVersionDiffs(TestCase):

    def test_get_version_diffs(self):
        versions = [
            {
                'user': 'john',
                'information_source': 'Manual correction by a user',
                'data': {
                    'a': 'alpha',
                    'b': 'beta',
                    'g': '',
                    'h': None,
                    'l': 'lambda',
                }
            },
            {
                'information_source': 'Updated by a script',
                'data': {
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
                'data': {
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
                'data': {
                    'a': 'alpha',
                    'b': 'beta',
                    'g': '',
                    'h': None,
                    'l': 'lambda',
                },
                'diff': [
                    {
                        'op': u'remove',
                        'path': 'd',
                        'previous_value': 'delta',
                    },
                    {
                        'op': u'replace',
                        'path': 'b',
                        'previous_value': 'LATIN SMALL LETTER B',
                        'value': 'beta',
                    }
                ]
            },
            {
                'information_source': 'Updated by a script',
                'data': {
                    'a': 'alpha',
                    'b': 'LATIN SMALL LETTER B',
                    'd': 'delta',
                    'g': None,
                    'h': '',
                    'l': 'lambda',
                },
                'diff': [
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
            },
            {
                'information_source': 'Original imported data',
                'data': {
                    'a': 'alpha',
                    'b': 'beta',
                    'l': None,
                },
                'diff': [
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
                ]
            },
        ]

        versions_with_diffs = get_version_diffs(versions)

        self.assertEqual(expected_result, versions_with_diffs)

    def test_versions_2010_then_adding_2015(self):
        versions = [
            {
                'information_source': 'After clicking "Standing again"',
                'data': {
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
                'data': {
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
                'data': {
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
                },
                'diff': [
                    {
                        'op': 'add',
                        'path': 'standing_in/2015',
                        'value': 'is known to be standing in Edinburgh North and Leith in 2015',
                    }
                ]
            },
            {
                'information_source': 'Original imported data',
                'data': {
                    'standing_in': {
                        '2010': {
                            'name': 'South Cambridgeshire',
                            'post_id': '65922',
                            'mapit_url': 'http://mapit.mysociety.org/area/65922',
                        },
                    }
                },
                'diff':[
                    {
                        'op': 'add',
                        'path': 'standing_in',
                        'value': 'was known to be standing in South Cambridgeshire in 2010',
                    }
                ]
            },
        ]

        versions_with_diffs = get_version_diffs(versions)

        self.assertEqual(expected_result, versions_with_diffs)

    def test_versions_2010_then_definitely_not_2015(self):
        versions = [
            {
                'information_source': 'After clicking "Not standing again"',
                'data': {
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
                'data': {
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
                'data': {
                    'standing_in': {
                        '2010': {
                            'name': 'South Cambridgeshire',
                            'post_id': '65922',
                            'mapit_url': 'http://mapit.mysociety.org/area/65922',
                        },
                        '2015': None,
                    }
                },
                'diff': [
                    {
                        'op': 'add',
                        'path': 'standing_in/2015',
                        'value': 'is known not to be standing in 2015',
                    }
                ]
            },
            {
                'information_source': 'Original imported data',
                'data': {
                    'standing_in': {
                        '2010': {
                            'name': 'South Cambridgeshire',
                            'post_id': '65922',
                            'mapit_url': 'http://mapit.mysociety.org/area/65922',
                        },
                    }
                },
                'diff':[
                    {
                        'op': 'add',
                        'path': 'standing_in',
                        'value': 'was known to be standing in South Cambridgeshire in 2010',
                    }
                ]
            },
        ]

        versions_with_diffs = get_version_diffs(versions)

        self.assertEqual(expected_result, versions_with_diffs)


    def test_versions_just_party_changed(self):
        versions = [
            {
                'information_source': 'After clicking "Not standing again"',
                'data': {
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
                'data': {
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
                'data': {
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
                'diff': [
                    {
                        'op': 'replace',
                        'path': 'party_memberships/2015/id',
                        'previous_value': 'is known to be standing for the party with ID party:58 in 2015',
                        'value': 'is known to be standing for the party with ID ynmp-party:2 in 2015',
                    },
                    {
                        'op': 'replace',
                        'path': 'party_memberships/2015/name',
                        'previous_value': 'is known to be standing for the party "Mebyon Kernow - The Party for Cornwall" in 2015',
                        'value': 'is known to be standing for the party "Independent" in 2015',
                    },
                ]
            },
            {
                'information_source': 'Original imported data',
                'data': {
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
                'diff':[
                    {
                        'op': 'add',
                        'path': 'party_memberships',
                        'value': 'is known to be standing for the party "Mebyon Kernow - The Party for Cornwall" in 2015 and was known to be standing for the party "Mebyon Kernow - The Party for Cornwall" in 2010',
                    }
                ]
            },
        ]

        versions_with_diffs = get_version_diffs(versions)

        self.assertEqual(expected_result, versions_with_diffs)
