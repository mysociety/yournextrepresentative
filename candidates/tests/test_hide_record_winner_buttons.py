from __future__ import unicode_literals

from django.test.utils import override_settings
from django_webtest import WebTest

from .auth import TestUserMixin
from .dates import (
    processors_before,
    processors_on_election_day,
    processors_after,
)
from .uk_examples import UK2015ExamplesMixin
from .factories import CandidacyExtraFactory, PersonExtraFactory


class TestWasElectedButtons(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestWasElectedButtons, self).setUp()
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

    @override_settings(TEMPLATE_CONTEXT_PROCESSORS=processors_before)
    def test_no_was_elected_button_before(self):
        response = self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user_who_can_record_results,
        )
        self.assertNotIn(
            '<input type="submit" class="button" value="This candidate was elected!">',
            response,
        )

    @override_settings(TEMPLATE_CONTEXT_PROCESSORS=processors_on_election_day)
    def test_show_was_elected_button_on_election_day(self):
        response = self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user_who_can_record_results,
        )
        self.assertIn(
            '<input type="submit" class="button" value="This candidate was elected!">',
            response,
        )

    @override_settings(TEMPLATE_CONTEXT_PROCESSORS=processors_after)
    def test_show_was_elected_button_after(self):
        response = self.app.get(
            '/election/2015/post/65808/dulwich-and-west-norwood',
            user=self.user_who_can_record_results,
        )
        self.assertIn(
            '<input type="submit" class="button" value="This candidate was elected!">',
            response,
        )
