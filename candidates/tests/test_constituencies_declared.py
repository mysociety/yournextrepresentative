from __future__ import unicode_literals

import re
from django_webtest import WebTest

from candidates.models import MembershipExtra

from .auth import TestUserMixin
from .factories import (
    CandidacyExtraFactory, MembershipFactory, PersonExtraFactory,
)
from .settings import SettingsMixin
from .uk_examples import UK2015ExamplesMixin


class TestConstituenciesDeclared(TestUserMixin, SettingsMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestConstituenciesDeclared, self).setUp()

        tessa_jowell = PersonExtraFactory.create(
            base__id='2009',
            base__name='Tessa Jowell'
        )
        CandidacyExtraFactory.create(
            election=self.election,
            base__person=tessa_jowell.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base
            )
        MembershipFactory.create(
            person=tessa_jowell.base,
            organization=self.labour_party_extra.base
        )

        winner = PersonExtraFactory.create(
            base__id='4322',
            base__name='Helen Hayes'
        )
        CandidacyExtraFactory.create(
            election=self.election,
            base__person=winner.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base,
            elected=True
            )
        MembershipFactory.create(
            person=winner.base,
            organization=self.labour_party_extra.base
        )

        james_smith = PersonExtraFactory.create(
            base__id='2010',
            base__name='James Smith'
        )
        CandidacyExtraFactory.create(
            election=self.election,
            base__person=james_smith.base,
            base__post=self.camberwell_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base
            )
        MembershipFactory.create(
            person=james_smith.base,
            organization=self.labour_party_extra.base
        )

    def test_constituencies_declared(self):
        response = self.app.get(
            '/election/2015/constituencies/declared'
        )

        self.assertEqual(response.status_code, 200)
        response.mustcontain('Dulwich')
        response.mustcontain('Camberwell')

        response.mustcontain('3 still undeclared (25% done)')

    def test_constituencies_declared_bad_election(self):
        response = self.app.get(
            '/election/2014/constituencies/declared',
            expect_errors=True
        )

        self.assertEqual(response.status_code, 404)

    def test_constituencies_appear_when_declared(self):
        response = self.app.get(
            '/election/2015/constituencies/declared'
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.search(
                r'''(?ms)<del><a[^>]*>Dulwich and West Norwood''',
                response.text
            )
        )
        self.assertTrue(
            re.search(
                r'''(?ms)<a[^>]*>Camberwell and Peckham''',
                response.text
            )
        )
        self.assertFalse(
            re.search(
                r'''(?ms)<del><a[^>]*>Camberwell and Peckham''',
                response.text
            )
        )
        response.mustcontain('3 still undeclared (25% done)')

        unelected = MembershipExtra.objects.filter(
            election=self.election,
            base__person_id=2010,
            base__post__extra__slug='65913'
        ).first()

        unelected.elected = True
        unelected.save()

        response = self.app.get(
            '/election/2015/constituencies/declared'
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            re.search(
                r'''(?ms)<del><a[^>]*>Dulwich and West Norwood''',
                response.text
            )
        )
        self.assertTrue(
            re.search(
                r'''(?ms)<del><a[^>]*>Camberwell and Peckham''',
                response.text
            )
        )
        response.mustcontain('2 still undeclared (50% done)')
