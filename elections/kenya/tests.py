# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django_webtest import WebTest
from nose.plugins.attrib import attr

from candidates.tests.factories import (
    AreaTypeFactory, ElectionFactory, ParliamentaryChamberExtraFactory,
)


@attr(country='kenya')
class KenyaTests(WebTest):

    def test_front_page(self):
        # Check that our custom search form label is actually present
        response = self.app.get('/')
        self.assertContains(response, 'Enter your county or constituency:')
