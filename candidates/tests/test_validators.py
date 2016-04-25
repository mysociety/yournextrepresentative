from __future__ import unicode_literals

from django.test import TestCase

from ..forms import BasePersonForm, UpdatePersonForm

from .factories import (
    AreaExtraFactory, AreaTypeFactory, ElectionFactory,
    ParliamentaryChamberExtraFactory, PartyFactory, PartyExtraFactory,
    PersonExtraFactory, PostExtraFactory, PartySetFactory,
    CandidacyExtraFactory, MembershipFactory
)
from .uk_examples import UK2015ExamplesMixin



class TestValidators(UK2015ExamplesMixin, TestCase):

    def setUp(self):
        wmc_area_type = AreaTypeFactory.create()
        gb_parties = PartySetFactory.create(slug='gb', name='Great Britain')
        commons = ParliamentaryChamberExtraFactory.create()

        election = ElectionFactory.create(
            slug='2015',
            name='2015 General Election',
            area_types=(wmc_area_type,),
            organization=commons.base
        )
        self.election = election
        PostExtraFactory.create(
            elections=(election,),
            base__organization=commons.base,
            slug='65808',
            base__label='Member of Parliament for Dulwich and West Norwood',
            party_set=gb_parties,
        )
        PartyExtraFactory.reset_sequence()
        PartyFactory.reset_sequence()
        self.parties = {}
        for i in range(0, 4):
            party_extra = PartyExtraFactory.create()
            gb_parties.parties.add(party_extra.base)
            self.parties[party_extra.slug] = party_extra

        dulwich_area_extra = AreaExtraFactory.create(
            base__identifier='65808',
            base__name='Dulwich and West Norwood',
            type=wmc_area_type,
        )

        post_extra = PostExtraFactory.create(
            elections=(election,),
            base__organization=commons.base,
            base__area=dulwich_area_extra.base,
            slug='65809',
            base__label='Member of Parliament for Dulwich and West Norwood',
            party_set=gb_parties,
        )

        person_extra = PersonExtraFactory.create(
            base__id='2009',
            base__name='Tessa Jowell'
        )

        self.person = person_extra.base

        CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_extra.base,
            base__post=post_extra.base,
            base__on_behalf_of=party_extra.base
            )
        MembershipFactory.create(
            person=person_extra.base,
            organization=party_extra.base
        )



    def tearDown(self):
        self.parties = {}
        super(TestValidators, self).setUp()

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
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'email': ['Enter a valid email address.']})

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
        })
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
        })
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
        })
        self.assertTrue(form.is_valid())
