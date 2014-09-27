import json
from os.path import dirname, join

from mock import patch

from django_webtest import WebTest

class FakeCollection(object):

    example_popit_data_directory = join(
        dirname(__file__), '..', 'example-popit-data'
    )

    def __init__(self, *args):
        self.object_id = args[0] if len(args) == 1 else None

    def get(self, **kwargs):
        with open(join(
                self.example_popit_data_directory,
                '{0}_{1}_embed={2}.json'.format(
                    self.collection,
                    self.object_id,
                    kwargs.get('embed', 'membership')
                )
        )) as f:
                return json.load(f)


class FakePersonCollection(FakeCollection):
    collection = 'persons'


class FakeOrganizationCollection(FakeCollection):
    collection = 'organizations'


class TestConstituencyDetailView(WebTest):

    @patch('candidates.views.PopIt')
    def test_any_constituency_page(self, mock_popit):
        mock_popit.return_value.organizations = FakeOrganizationCollection
        mock_popit.return_value.persons = FakePersonCollection
        # Just a smoke test for the moment:
        response = self.app.get('/constituency/65808/dulwich-and-west-norwood')
        response.mustcontain('Tessa Jowell (Labour Party)')
