# Smoke tests for viewing a candidate's page

import re

from mock import patch

from django_webtest import WebTest

from .fake_popit import FakePersonCollection

@patch('candidates.popit.PopIt')
class TestPersonView(WebTest):

    def test_get_tessa_jowell(self, mock_popit):
        mock_popit.return_value.persons = FakePersonCollection
        response = self.app.get('/person/2009/tessa-jowell')
        self.assertTrue(
            re.search(
                r'''(?msx)
  <h1>Tessa\ Jowell</h1>\s*
  <p>Candidate\ for
  \ <a\ href="/constituency/65808/dulwich-and-west-norwood">Dulwich
  \ and\ West\ Norwood</a>\ in\ 2015</p>''',
                unicode(response)
            )
        )

    def test_get_non_existent(self, mock_popit):
        mock_popit.return_value.persons = FakePersonCollection
        response = self.app.get(
            '/person/987654/imaginary-person',
            expect_errors=True
        )
        self.assertEqual(response.status_code, 404)
