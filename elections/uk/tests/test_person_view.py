from __future__ import unicode_literals

import re

from django.test.utils import override_settings
from django_webtest import WebTest

from nose.plugins.attrib import attr

from candidates.tests.auth import TestUserMixin
from candidates.tests.dates import processors_before, processors_after
from candidates.tests.factories import (
    CandidacyExtraFactory, PersonExtraFactory
)
from candidates.tests.uk_examples import UK2015ExamplesMixin


@attr(country='uk')
class TestPersonView(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestPersonView, self).setUp()
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

    def test_get_tessa_jowell(self):
        response = self.app.get('/person/2009/tessa-jowell')
        self.assertTrue(
            re.search(
                r'''(?msx)
  <h1>Tessa\s+Jowell</h1>\s*
  <p>Candidate\s+for\s+
  <a\s+href="/election/2015/post/65808/dulwich-and-west-norwood">Dulwich\s+
  and\s+West\s+Norwood</a>\s+in\ <a\ href="/election/2015/constituencies">2015
  \s+General\s+Election</a>\s*</p>''',
                response.text
            )
        )

    @override_settings(TEMPLATE_CONTEXT_PROCESSORS=processors_before)
    def test_get_tessa_jowell_before_election(self):
        response = self.app.get('/person/2009/tessa-jowell')
        self.assertContains(response, 'Contesting the 2015 General Election')

    @override_settings(TEMPLATE_CONTEXT_PROCESSORS=processors_after)
    def test_get_tessa_jowell_after_election(self):
        response = self.app.get('/person/2009/tessa-jowell')
        self.assertContains(response, 'Contested the 2015 General Election')

    def test_get_non_existent(self):
        response = self.app.get(
            '/person/987654/imaginary-person',
            expect_errors=True
        )
        self.assertEqual(response.status_code, 404)

    def test_shows_no_edit_buttons_if_user_not_authenticated(self):
        response = self.app.get('/person/2009/tessa-jowell')
        edit_buttons = response.html.find_all('a', attrs={'class': 'button'})
        self.assertEqual(len(edit_buttons), 1)
        self.assertEqual(edit_buttons[0].string, 'Log in to edit')

    def test_shows_edit_buttons_if_user_authenticated(self):
        response = self.app.get('/person/2009/tessa-jowell', user=self.user)
        edit_buttons = response.html.find_all('a', attrs={'class': 'button'})
        self.assertEqual(len(edit_buttons), 2)

    def test_links_to_person_edit_page(self):
        response = self.app.get('/person/2009/tessa-jowell', user=self.user)
        self.assertContains(response, 'href="/person/2009/update"')

    def test_links_to_person_photo_upload_page(self):
        response = self.app.get('/person/2009/tessa-jowell', user=self.user)
        self.assertContains(response, 'href="/moderation/photo/upload/2009"')
