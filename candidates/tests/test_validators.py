from django.test import TestCase

from ..forms import BasePersonForm, UpdatePersonForm

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

    def test_update_person_form_standing_no_party_no_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing': 'standing',
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            '__all__':
            [u'If you mark the candidate as standing in 2015, you must select a constituency']
        })

    def test_update_person_form_standing_no_party_but_gb_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing': 'standing',
            'constituency': '65808',
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            '__all__':
            [u'You must specify a party for the 2015 election']
        })

    def test_update_person_form_standing_party_and_gb_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing': 'standing',
            'constituency': '65808',
            'party_gb': 'party:52',
        })
        self.assertTrue(form.is_valid())

    # When 'not-standing' is selected, it shouldn't matter whether you
    # specify party of constituency:

    def test_update_person_form_not_standing_no_party_no_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing': 'not-standing',
        })
        self.assertTrue(form.is_valid())

    def test_update_person_form_not_standing_no_party_but_gb_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing': 'not-standing',
            'constituency': '65808',
        })
        self.assertTrue(form.is_valid())

    def test_update_person_form_not_standing_party_and_gb_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing': 'standing',
            'constituency': '65808',
            'party_gb': 'party:52',
        })
        self.assertTrue(form.is_valid())

    # Similarly, when 'not-sure' is selected, it shouldn't matter
    # whether you specify party of constituency:

    def test_update_person_form_not_sure_no_party_no_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing': 'not-sure',
        })
        self.assertTrue(form.is_valid())

    def test_update_person_form_not_sure_no_party_but_gb_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing': 'not-sure',
            'constituency': '65808',
        })
        self.assertTrue(form.is_valid())

    def test_update_person_form_not_sure_party_and_gb_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing': 'not-sure',
            'constituency': '65808',
            'party_gb': 'party:52',
        })
        self.assertTrue(form.is_valid())
