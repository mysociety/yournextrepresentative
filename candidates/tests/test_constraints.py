from __future__ import unicode_literals

from django.test import TestCase
from popolo.models import Post

from ..models import check_paired_models
from .uk_examples import UK2015ExamplesMixin


class PairedConstraintCheckTests(UK2015ExamplesMixin, TestCase):

    def test_no_problems_normally(self):
        errors = check_paired_models()
        for e in errors:
            print e
        self.assertEqual(0, len(errors))

    def test_base_with_no_extra_detected(self):
        unpaired_post = Post.objects.create(organization=self.commons)
        expected_errors = [
            'There were 5 Post objects, but 4 PostExtra objects',
            'The Post object with ID {} had no corresponding ' \
            'PostExtra object'.format(unpaired_post.id)
            ]
        self.assertEqual(
            check_paired_models(),
            expected_errors)
