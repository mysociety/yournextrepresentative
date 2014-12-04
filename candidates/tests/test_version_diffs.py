from django.test import TestCase

from ..models import get_version_diffs

class TestVersionDiffs(TestCase):

    def test_get_version_diffs(self):
        versions = [
            {
                'user': 'john',
                'information_source': 'Manual correction by a user',
                'data': {
                    'a': 'alpha',
                    'b': 'beta',
                }
            },
            {
                'information_source': 'Updated by a script',
                'data': {
                    'a': 'alpha',
                    'b': 'LATIN SMALL LETTER B',
                    'd': 'delta',
                }
            },
            {
                'information_source': 'Original imported data',
                'data': {
                    'a': 'alpha',
                    'b': 'beta',
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
                },
                'diff': [
                    {
                        'op': u'remove',
                        'path': '/d',
                        'previous_value': 'delta',
                    },
                    {
                        'op': u'replace',
                        'path': '/b',
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
                },
                'diff': [
                    {
                        'op': 'add',
                        'path': '/d',
                        'value': 'delta',
                    },
                    {
                        'op': 'replace',
                        'path': '/b',
                        'previous_value': 'beta',
                        'value': 'LATIN SMALL LETTER B',
                    }
                ]
            },
            {
                'information_source': 'Original imported data',
                'data': {
                    'a': 'alpha',
                    'b': 'beta',
                },
                'diff': [
                    {
                        'op': 'add',
                        'path': '/a',
                        'value': 'alpha',
                    },
                    {
                        'op': 'add',
                        'path': '/b',
                        'value': 'beta',
                    },
                ]
            },
        ]

        versions_with_diffs = get_version_diffs(versions)

        self.assertEqual(expected_result, versions_with_diffs)
