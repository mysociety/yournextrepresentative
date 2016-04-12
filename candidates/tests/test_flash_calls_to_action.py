from __future__ import unicode_literals

import re

from django.test import TestCase

from candidates.views.people import get_call_to_action_flash_message

from . import factories
from .uk_examples import UK2015ExamplesMixin

def normalize_whitespace(s):
    return re.sub(r'(?ms)\s+', ' ', s)

class TestGetFlashMessage(UK2015ExamplesMixin, TestCase):

    maxDiff = None

    def setUp(self):
        super(TestGetFlashMessage, self).setUp()
        self.fake_person_extra = factories.PersonExtraFactory.create(
            base__name='Wreck-it-Ralph',
            base__id=42,
        )
        post_extra_in_2010 = self.edinburgh_east_post_extra
        post_extra_in_2015 = self.edinburgh_north_post_extra
        factories.CandidacyExtraFactory.create(
            election=self.election,
            base__person=self.fake_person_extra.base,
            base__post=post_extra_in_2010.base,
        )
        factories.CandidacyExtraFactory.create(
            election=self.earlier_election,
            base__person=self.fake_person_extra.base,
            base__post=post_extra_in_2015.base,
        )

    def test_get_flash_message_new_person(self):
        self.assertEqual(
            ' Thank-you for adding <a href="/person/42">Wreck-it-Ralph</a>! '
            'Now you can carry on to:'
            ' <ul> <li> <a href="/person/42/update">Edit Wreck-it-Ralph again</a> </li>'
            ' <li> Add a candidate for <a href="/numbers/attention-needed">one '
            'of the posts with fewest candidates</a> </li>'
            ' <li> <a href="/election/2015/person/create/">Add another '
            'candidate in the 2015 General Election</a> </li> </ul> ',
            normalize_whitespace(
                get_call_to_action_flash_message(
                    self.fake_person_extra.base,
                    new_person=True
                )
            )
        )

    def test_get_flash_message_updated_person(self):
        self.assertEqual(
            ' Thank-you for updating <a href="/person/42">Wreck-it-Ralph</a>! '
            'Now you can carry on to:'
            ' <ul> <li> <a href="/person/42/update">Edit Wreck-it-Ralph again</a> </li>'
            ' <li> Add a candidate for <a href="/numbers/attention-needed">one '
            'of the posts with fewest candidates</a> </li>'
            ' <li> <a href="/election/2015/person/create/">Add another '
            'candidate in the 2015 General Election</a> </li> </ul> ',
            normalize_whitespace(
                get_call_to_action_flash_message(
                    self.fake_person_extra.base,
                    new_person=False
                )
            )
        )
