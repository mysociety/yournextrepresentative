import json
from os.path import dirname, join
import re
from urlparse import urlsplit

from mock import MagicMock

example_popit_data_directory = join(
    dirname(__file__), '..', 'example-popit-data'
)

def get_example_popit_json(basename):
    with open(
        join(example_popit_data_directory, basename)
    ) as f:
        return json.load(f)

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
