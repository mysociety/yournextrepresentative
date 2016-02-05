# -*- coding: utf-8 -*-
from mock import patch

from django_webtest import WebTest
from nose.plugins.attrib import attr

from candidates.tests.factories import (
    AreaTypeFactory, ElectionFactory, ParliamentaryChamberExtraFactory,
)


@attr(country='cr')
class CostaRicaTests(WebTest):

    def setUp(self):
        area_type = AreaTypeFactory.create()
        org = ParliamentaryChamberExtraFactory.create()

        self.election = ElectionFactory.create(
            slug='cr-2015',
            name='2015 Election',
            area_types=(area_type,),
            organization=org.base
        )

    def test_front_page(self):
        # Just a smoke test, e.g. to check that all the assets
        # required are present...
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    @patch('elections.cr.views.Election.objects.are_upcoming_elections')
    def test_frontpage_changes_pre_election(self, mock_upcoming):
        mock_upcoming.return_value = True
        response = self.app.get('/')
        self.assertContains(response, 'upcoming municipal elections')

    @patch('elections.cr.views.Election.objects.are_upcoming_elections')
    def test_frontpage_changes_after_election(self, mock_upcoming):
        mock_upcoming.return_value = False
        response = self.app.get('/')
        self.assertContains(response, 'candidates who stood in the elections')
