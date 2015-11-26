# -*- coding: utf-8 -*-

from django_webtest import WebTest
from unittest import skip


@skip('Need to write replacement API using popolo-django')
class TestApiHelpView(WebTest):
      def test_api_help(self):
          response = self.app.get('/help/api')
          self.assertEqual(response.status_code, 200)

          # check for the all candidates link
          self.assertIn(
              'Download of the candidates for all elections',
              response)

          # check for the all candidates link
          self.assertIn(
              'Download of the 2015 General Election candidates',
              response)
