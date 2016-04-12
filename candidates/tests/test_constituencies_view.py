from __future__ import unicode_literals

import re

from django_webtest import WebTest

from .uk_examples import UK2015ExamplesMixin

class TestConstituencyDetailView(UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestConstituencyDetailView, self).setUp()

    def test_constituencies_page(self):
        # Just a smoke test to check that the page loads:
        response = self.app.get('/election/2015/constituencies')
        dulwich= response.html.find(
            'a', text=re.compile(r'Dulwich and West Norwood')
        )
        self.assertTrue(dulwich)
