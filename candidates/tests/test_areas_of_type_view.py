# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re

from django_webtest import WebTest

from .auth import TestUserMixin

from .factories import (
    AreaExtraFactory, CandidacyExtraFactory, PersonExtraFactory,
    PostExtraFactory,
)
from .uk_examples import UK2015ExamplesMixin

class TestAreasOfTypeView(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestAreasOfTypeView, self).setUp()
        person_extra = PersonExtraFactory.create(
            base__id='2009',
            base__name='Tessa Jowell'
        )
        CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_extra.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base
            )

        aldershot_area_extra = AreaExtraFactory.create(
            base__identifier='65730',
            type=self.wmc_area_type,
        )
        PostExtraFactory.create(
            elections=(self.election,),
            base__area=aldershot_area_extra.base,
            base__organization=self.commons,
            slug='65730',
            base__label='Member of Parliament for Aldershot',
            party_set=self.gb_parties,
        )

    def test_any_areas_of_type_page_without_login(self):
        response = self.app.get('/areas-of-type/WMC/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.search(
                r'''(?msx)
  <a\s+href="/areas/WMC--65808/dulwich-and-west-norwood">
  Dulwich\s+and\s+West\s+Norwood</a>''',
                response.text
            )
        )

    def test_get_malformed_url(self):
        response = self.app.get(
            '/areas-of-type/3243452345/invalid',
            expect_errors=True
        )
        self.assertEqual(response.status_code, 404)


    def test_get_non_existent(self):
        response = self.app.get(
            '/areas-of-type/AAA/',
            expect_errors=True
        )
        self.assertEqual(response.status_code, 404)
