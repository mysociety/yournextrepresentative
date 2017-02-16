from __future__ import unicode_literals

from unittest import skip

from django.test import TestCase

from ..forms import BasePersonForm, UpdatePersonForm

from .factories import PersonExtraFactory
from .uk_examples import UK2015ExamplesMixin


class TestValidators(UK2015ExamplesMixin, TestCase):

    def setUp(self):
        super(TestValidators, self).setUp()
        self.person = PersonExtraFactory.create(base__name='John Doe').base

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
                ['The Twitter username must only consist of alphanumeric characters or underscore']
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

    def test_malformed_email(self):
        form = BasePersonForm({
            'name': 'John Bercow',
            'email': 'foo bar!',
        }, initial={'person': self.person,})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'email': ['Enter a valid email address.']})

    @skip("Until rebased over upstream master")
    def test_update_person_form_standing_no_party_no_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing_2015': 'standing',
        }, initial={'person': self.person,})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            '__all__':
            ['If you mark the candidate as standing in the 2015 General Election, you must select a post']
        })

    @skip("Until rebased over upstream master")
    def test_update_person_form_standing_no_party_but_gb_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing_2015': 'standing',
            'constituency_2015': '65808',
        }, initial={'person': self.person,})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            '__all__':
            ['You must specify a party for the 2015 General Election']
        })

    def test_update_person_form_standing_party_and_gb_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing_2015': 'standing',
            'constituency_2015': '65808',
            'party_gb_2015': self.conservative_party_extra.base.id,
        }, initial={'person': self.person,})
        self.assertTrue(form.is_valid())

    # When 'not-standing' is selected, it shouldn't matter whether you
    # specify party of constituency:

    def test_update_person_form_not_standing_no_party_no_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing_2015': 'not-standing',
        }, initial={'person': self.person,})
        self.assertTrue(form.is_valid())

    def test_update_person_form_not_standing_no_party_but_gb_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing_2015': 'not-standing',
            'constituency_2015': '65808',
        }, initial={'person': self.person,})
        self.assertTrue(form.is_valid())

    def test_update_person_form_not_standing_party_and_gb_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing_2015': 'standing',
            'constituency_2015': '65808',
            'party_gb_2015': self.conservative_party_extra.base.id,
        }, initial={'person': self.person,})
        self.assertTrue(form.is_valid())

    # Similarly, when 'not-sure' is selected, it shouldn't matter
    # whether you specify party of constituency:

    def test_update_person_form_not_sure_no_party_no_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing_2015': 'not-sure',
        }, initial={'person': self.person,})
        self.assertTrue(form.is_valid())

    def test_update_person_form_not_sure_no_party_but_gb_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing_2015': 'not-sure',
            'constituency_2015': '65808',
        }, initial={'person': self.person,})
        self.assertTrue(form.is_valid())

    def test_update_person_form_not_sure_party_and_gb_constituency(self):
        form = UpdatePersonForm({
            'name': 'John Doe',
            'source': 'Just testing...',
            'standing_2015': 'not-sure',
            'constituency_2015': '65808',
            'party_gb_2015': self.conservative_party_extra.base.id,
        }, initial={'person': self.person,})
        self.assertTrue(form.is_valid())
