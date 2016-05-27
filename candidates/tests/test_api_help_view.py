# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django_webtest import WebTest

from .settings import SettingsMixin
from . import factories

class TestApiHelpView(SettingsMixin, WebTest):

    def setUp(self):
        super(TestApiHelpView, self).setUp()
        factories.ElectionFactory.create(
            slug='2015',
            name='2015 General Election',
        )

    def test_api_help(self):
        response = self.app.get('/help/api')
        self.assertEqual(response.status_code, 200)

        self.assertIn(
            'Download of the 2015 General Election candidates',
            response)

        self.assertIn(
            "The browsable base URL of the site's read-only API is: <a href=\"http://localhost:80/api/v0.9/\">http://localhost:80/api/v0.9/</a>",
            response
        )
