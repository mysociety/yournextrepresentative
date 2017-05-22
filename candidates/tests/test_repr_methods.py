from __future__ import unicode_literals

from django.test import TestCase

from .uk_examples import UK2015ExamplesMixin


class TestReprMethods(UK2015ExamplesMixin, TestCase):

    def test_logged_action_repr(self):
        pee = self.camberwell_post_extra.postextraelection_set.get(
            election=self.election
        )
        self.assertEqual(
            repr(pee),
            "<PostExtraElection election__slug='2015' postextra__slug='65913'>",
        )

    def test_logged_action_repr_locked_with_winner_count(self):
        pee = self.camberwell_post_extra.postextraelection_set.get(
            election=self.election
        )
        pee.winner_count = 4
        pee.candidates_locked = True
        pee.save()
        self.assertEqual(
            repr(pee),
            "<PostExtraElection election__slug='2015' postextra__slug='65913' candidates_locked=True winner_count=4>",
        )
