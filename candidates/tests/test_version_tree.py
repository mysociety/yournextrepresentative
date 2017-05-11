from django.test import TestCase

from candidates.models.versions import get_versions_parent_map


class TestVersionTree(TestCase):

    def test_simple_linear_single_id(self):
        versions = [
            {
                "data": {
                    "id": "2009",
                },
                "information_source": "Found her Wikipedia page through Google",
                "timestamp": "2014-11-25T10:02:40.184563",
                "username": "user",
                "version_id": "407db6845dbb0007"
            },
            {
                "data": {
                    "id": "2009",
                },
                "information_source": "It says she's standing down here: http://www.bbc.co.uk/news/uk-politics-25045746",
                "timestamp": "2014-11-23T18:09:11.604997",
                "username": "mark",
                "version_id": "36198267ad42acb1"
            },
            {
                "data": {
                    "id": "2009",
                },
                "information_source": "Imported from YourNextMP data from 2010",
                "timestamp": "2014-11-21T18:16:48.116236",
                "version_id": "53e1260ec3946bbf"
            }
        ]
        self.assertEqual(
            get_versions_parent_map(versions),
            {
                '407db6845dbb0007': ['36198267ad42acb1'],
                '36198267ad42acb1': ['53e1260ec3946bbf'],
                '53e1260ec3946bbf': [],
            }
        )

    def test_single_merge(self):
        versions = [
            {
                "data": {
                    "id": "4",
                },
                "information_source": "Approved a photo upload from a script who provided the message: \"Auto imported from Twitter\"",
                "timestamp": "2016-05-01T19:35:44.838011",
                "username": "j0e_m",
                "version_id": "086bab0dbcbff4d1"
            },
            {
                "data": {
                    "id": "4",
                },
                "information_source": "Updated by the automated Twitter account checker (candidates_update_twitter_usernames)",
                "timestamp": "2016-04-28T08:46:05.352089",
                "version_id": "016b59341d65b9dc"
            },
            {
                "data": {
                    "id": "4",
                },
                "information_source": "more up to date email address from merged candidate page",
                "timestamp": "2016-04-23T14:30:30.328947",
                "username": "JeniT",
                "version_id": "7c4e8a767f45a0ab"
            },
            {
                "data": {
                    "id": "4",
                },
                "information_source": "After merging person 6628",
                "timestamp": "2016-04-23T14:28:53.499803",
                "username": "JeniT",
                "version_id": "4df120ba2cb9042c"
            },
            {
                "data": {
                    "id": "4",
                },
                "information_source": "There's a Labour candidate already listed for Rushcliffe on this site, plus you also show Andrew Clayworth standing as the TUSC candidate in Nottingham South.",
                "timestamp": "2015-03-21T00:16:33.324290",
                "username": "greenm2",
                "version_id": "6eaf38ba8f30f68c"
            },
            {
                "data": {
                    "id": "4",
                },
                "information_source": "Imported from YourNextMP data from 2010",
                "timestamp": "2014-11-21T18:07:15.616170",
                "version_id": "5a30bda120ae89b1"
            },
            {
                "data": {
                    "id": "6628",
                },
                "information_source": "http://tusc2015.com/andrew-clayworth-for-nottingham-south/",
                "timestamp": "2016-04-23T14:26:34.673240",
                "username": "JeniT",
                "version_id": "4ce77239a3ce82f4"
            },
            {
                "data": {
                    "id": "6628",
                },
                "information_source": "[Quick update from the constituency page]",
                "timestamp": "2015-05-08T05:25:31.230573",
                "username": "symroe",
                "version_id": "1dd9756a410cdc3c"
            },
            {
                "data": {
                    "id": "6628",
                },
                "information_source": "Approved a photo upload from TUSCNottmSouth who provided the message: \"\"",
                "timestamp": "2015-04-17T09:19:15.053401",
                "username": "mark",
                "version_id": "3d75507f7f81411d"
            },
            {
                "data": {
                    "id": "6628",
                },
                "information_source": "The candidate",
                "timestamp": "2015-04-16T23:32:31.301827",
                "username": "TUSCNottmSouth",
                "version_id": "23a5014297200590"
            },
            {
                "data": {
                    "id": "6628",
                },
                "information_source": "http://www.tusc.org.uk/txt/324.pdf",
                "timestamp": "2015-03-05T14:45:03.058131",
                "username": "bwdeacon",
                "version_id": "5abf454b55e734a5"
            }
        ]
        self.assertEqual(
            get_versions_parent_map(versions),
            {
                # The versions with ID 6628:
                '5abf454b55e734a5': [],
                '23a5014297200590': ['5abf454b55e734a5'],
                '3d75507f7f81411d': ['23a5014297200590'],
                '1dd9756a410cdc3c': ['3d75507f7f81411d'],
                '4ce77239a3ce82f4': ['1dd9756a410cdc3c'],
                # Now the versions with ID 4:
                '5a30bda120ae89b1': [],
                '6eaf38ba8f30f68c': ['5a30bda120ae89b1'],
                # This was the version representing the merge:
                '4df120ba2cb9042c': ['6eaf38ba8f30f68c', '4ce77239a3ce82f4'],
                '7c4e8a767f45a0ab': ['4df120ba2cb9042c'],
                '016b59341d65b9dc': ['7c4e8a767f45a0ab'],
                '086bab0dbcbff4d1': ['016b59341d65b9dc'],
            }
        )

    def test_secondary_history_missing(self):
        versions = [
            {
                "data": {
                    "id": "2009",
                },
                "information_source": "After merging person 123456789",
                "timestamp": "2014-11-25T10:02:40.184563",
                "username": "user",
                "version_id": "407db6845dbb0007"
            },
            {
                "data": {
                    "id": "2009",
                },
                "information_source": "It says she's standing down here: http://www.bbc.co.uk/news/uk-politics-25045746",
                "timestamp": "2014-11-23T18:09:11.604997",
                "username": "mark",
                "version_id": "36198267ad42acb1"
            },
            {
                "data": {
                    "id": "2009",
                },
                "information_source": "Imported from YourNextMP data from 2010",
                "timestamp": "2014-11-21T18:16:48.116236",
                "version_id": "53e1260ec3946bbf"
            }
        ]
        self.assertEqual(
            get_versions_parent_map(versions),
            {
                '53e1260ec3946bbf': [],
                '36198267ad42acb1': ['53e1260ec3946bbf'],
                '407db6845dbb0007': ['36198267ad42acb1'],
            }
        )

    def test_other_person_earlier(self):
        versions = [
            {
                "data": {
                    "id": "2009",
                },
                "information_source": "Some random update",
                "timestamp": "2014-11-25T10:02:40.184563",
                "username": "user",
                "version_id": "407db6845dbb0007"
            },
            {
                "data": {
                    "id": "2009",
                },
                "information_source": "After merging person 567",
                "timestamp": "2014-11-24T10:02:40.184563",
                "username": "user",
                "version_id": "43eb6cd97a180e4a"

            },
            {
                "data": {
                    "id": "2009",
                },
                "information_source": "It says she's standing down here: http://www.bbc.co.uk/news/uk-politics-25045746",
                "timestamp": "2014-11-23T18:09:11.604997",
                "username": "mark",
                "version_id": "36198267ad42acb1"
            },
            {
                "data": {
                    "id": "2009",
                },
                "information_source": "Imported from YourNextMP data from 2010",
                "timestamp": "2014-11-21T18:16:48.116236",
                "version_id": "53e1260ec3946bbf"
            },
            {
                "data": {
                    "id": "567",
                },
                "information_source": "Spotted on the interwebs!",
                "timestamp": "2014-10-02T19:03:10.236114",
                "version_id": "3787faf978dee092"
            },            
        ]
        self.assertEqual(
            get_versions_parent_map(versions),
            {
                # The versions with ID 2009:
                '407db6845dbb0007': ['43eb6cd97a180e4a'],
                # The merge:
                '43eb6cd97a180e4a': ['36198267ad42acb1', '3787faf978dee092'],
                '36198267ad42acb1': ['53e1260ec3946bbf'],
                '53e1260ec3946bbf': [],
                # The older, but secondary version with ID 567:
                '3787faf978dee092': [],
            }
        )

    def test_bogus_merge_extraneous(self):
        versions = [
            {
                "data": {
                    "id": "2009",
                },
                "information_source": "After merging person 567",
                "timestamp": "2014-11-26T10:02:40.184563",
                "username": "user",
                "version_id": "1164b8bcedb1a1e6"
            },
            {
                "data": {
                    "id": "2009",
                },
                "information_source": "Some random update",
                "timestamp": "2014-11-25T10:02:40.184563",
                "username": "user",
                "version_id": "407db6845dbb0007"
            },
            {
                "data": {
                    "id": "2009",
                },
                "information_source": "After merging person 567",
                "timestamp": "2014-11-24T10:02:40.184563",
                "username": "user",
                "version_id": "43eb6cd97a180e4a"

            },
            {
                "data": {
                    "id": "2009",
                },
                "information_source": "It says she's standing down here: http://www.bbc.co.uk/news/uk-politics-25045746",
                "timestamp": "2014-11-23T18:09:11.604997",
                "username": "mark",
                "version_id": "36198267ad42acb1"
            },
            {
                "data": {
                    "id": "2009",
                },
                "information_source": "Imported from YourNextMP data from 2010",
                "timestamp": "2014-11-21T18:16:48.116236",
                "version_id": "53e1260ec3946bbf"
            },
            {
                "data": {
                    "id": "567",
                },
                "information_source": "Spotted on the interwebs!",
                "timestamp": "2014-10-02T19:03:10.236114",
                "version_id": "3787faf978dee092"
            },
            
        ]
        with self.assertRaisesRegexp(
                Exception,
                r'It looks like there was a bogus merge version for person ' \
                r'with ID 2009; there were 2 merge versions and 2 person IDs.'
        ):
            get_versions_parent_map(versions)
