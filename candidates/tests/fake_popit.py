import json
from os.path import dirname, join
import re
from urlparse import urlsplit

from mock import Mock

example_popit_data_directory = join(
    dirname(__file__), '..', 'example-popit-data'
)

def get_example_popit_json(basename):
    with open(
        join(example_popit_data_directory, basename)
    ) as f:
        return json.load(f)

# In many cases we could get away without these fake PopIt API
# collection objects; for example, if you only need to return data on
# one organization in your test, and do a fetch of all people, you
# could do that with:
#
#   In [1]: from mock import Mock
#
#   In [2]: api = Mock(**{
#      ...:     'organizations.return_value.get.return_value': 'got-particular-org',
#      ...:     'persons.get.return_value': 'got-all-people'
#      ...: })
#
#   In [3]: api.organizations('national-assembly').get()
#   Out[3]: 'got-particular-org'
#
#   In [4]: api.organizations.get()
#   Out[4]: <Mock name='mock.organizations.get()' id='140711747445328'>
#
#   In [5]: api.persons.get()
#   Out[5]: 'got-all-people'
#
#   In [6]: api.persons('john-doe').get()
#   Out[6]: <Mock name='mock.persons().get()' id='140711747546640'>
#
# But that would return 'got-particular-org' no matter what ID was
# passed to api.organizations.

class FakeCollection(object):

    def __init__(self, *args):
        self.object_id = args[0] if len(args) == 1 else None

    def get(self, **kwargs):
        return get_example_popit_json(
            '{0}_{1}_embed={2}.json'.format(
                self.collection,
                self.object_id,
                kwargs.get('embed', 'membership')))

    def put(self, data):
        raise Exception("Not implemented: you should patch this")

    @staticmethod
    def post(data):
        raise Exception("Not implemented: you should patch this")


class FakePersonCollection(FakeCollection):
    collection = 'persons'


class FakeOrganizationCollection(FakeCollection):
    collection = 'organizations'

# This is used to fake results make via requests.get to the PopIt API.

def fake_get_result(url):
    split = urlsplit(url)
    m = re.search('/api/v0.1/(.*)', split.path)
    if not m:
        raise Exception, "Unexpected URL to fake_get_result: {0}".format(url)
    api_query = m.group(1)
    if api_query == 'search/organizations':
        if split.query == 'q=classification%3AParty%20AND%20name%3A%22Labour%20Party%22':
            json_result = get_example_popit_json('search_organization_labour_party.json')
        elif split.query == 'q=classification%3AParty%20AND%20name%3A%22Labour%22':
            json_result = get_example_popit_json('search_organization_labour.json')
        else:
            message = "Unexpected organization search query to fake_get_result {0}"
            raise Exception, message.format(split.query)
    else:
        raise Exception, "Unexpected API query to fake_get_result: {0}".format(api_query)
    return Mock(**{'json.return_value': json_result})
