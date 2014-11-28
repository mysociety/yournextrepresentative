from django.test import TestCase

from ..forms import BasePersonForm

class TestValidators(TestCase):

    def test_twitter_bad_url(self):
        form = BasePersonForm({
            'name': 'John Doe',
            'twitter_username': 'http://example.org/blah',
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                'twitter_username':
                [u'The Twitter username must only consist of alphanumeric characters or underscore']
            }
        )

    def test_twitter_fine(self):
        form = BasePersonForm({
            'name': 'John Doe',
            'twitter_username': 'madeuptwitteraccount',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.errors, {})
        self.assertEqual(
            form.cleaned_data['twitter_username'],
            'madeuptwitteraccount'
        )

    def test_twitter_full_url(self):
        form = BasePersonForm({
            'name': 'John Doe',
            'twitter_username': 'https://twitter.com/madeuptwitteraccount',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.errors, {})
        self.assertEqual(
            form.cleaned_data['twitter_username'],
            'madeuptwitteraccount'
        )

    def test_non_parliament_email(self):
        form = BasePersonForm({
            'name': 'John Doe',
            'email': 'foo@example.org',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data['email'],
            'foo@example.org',
        )

    def test_parliament_email(self):
        form = BasePersonForm({
            'name': 'John Bercow',
            'email': 'john.bercow.mp@parliament.uk',
        })
        self.assertFalse(form.is_valid())
        error_message = u"parliament.uk email addresses aren't useful once "
        error_message += u"parliament dissolves; please try to find an "
        error_message += u"alternative"
        self.assertEqual(form.errors, {'email': [error_message]})

    def test_malformed_email(self):
        form = BasePersonForm({
            'name': 'John Bercow',
            'email': 'foo bar!',
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'email': ['Enter a valid email address.']})
