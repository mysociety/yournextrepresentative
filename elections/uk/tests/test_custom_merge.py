from django_webtest import WebTest
from nose.plugins.attrib import attr
from popolo.models import Person

from candidates.tests import factories
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin

from uk_results.models import CandidateResult, PostResult, ResultSet


@attr(country='uk')
class TestUKResultsPreserved(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestUKResultsPreserved, self).setUp()
        self.primary_person = factories.PersonExtraFactory.create(
            base__id='3885',
            base__name='Harriet Harman'
        ).base
        self.secondary_person = factories.PersonExtraFactory.create(
            base__id='10000',
            base__name='Harriet Ruth Harman',
        ).base
        # And an extra election to create a candidacy of:
        local_council = factories.OrganizationExtraFactory.create(
            base__name='Maidstone',
            slug='local-authority:maidstone',
        ).base
        self.local_election = factories.ElectionFactory.create(
            slug='local.maidstone.2016-05-05',
            organization=local_council,
        )
        self.local_post = factories.PostExtraFactory.create(
            elections=(self.local_election,),
            slug='DIW:E05005004',
            base__label='Shepway South Ward',
            party_set=self.gb_parties,
            base__organization=local_council,
        )

    def test_uk_results_for_secondary_preserved(self):
        factories.CandidacyExtraFactory.create(
            election=self.earlier_election,
            base__person=self.primary_person,
            base__post=self.camberwell_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base,
        )
        factories.CandidacyExtraFactory.create(
            election=self.local_election,
            base__person=self.secondary_person,
            base__post=self.local_post.base,
            base__on_behalf_of=self.labour_party_extra.base,
        )
        secondary_membership_extra = factories.CandidacyExtraFactory.create(
            election=self.election,
            base__person=self.secondary_person,
            base__post=self.camberwell_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base,
        )

        # Now attach a vote count to the secondary person's candidacy:
        post_result = PostResult.objects.create(
            post=secondary_membership_extra.base.post,
            confirmed=False,
        )
        result_set = ResultSet.objects.create(
            post_result=post_result,
            num_turnout_reported=51561,
            num_spoilt_ballots=42,
            ip_address='127.0.0.1',
        )
        CandidateResult.objects.create(
            result_set=result_set,
            membership=secondary_membership_extra.base,
            num_ballots_reported=32614,
            is_winner=True,
        )
        # Now try the merge:
        response = self.app.get(
            '/person/3885/update',
            user=self.user_who_can_merge)
        merge_form = response.forms['person-merge']
        merge_form['other'] = '10000'
        response = merge_form.submit()

        self.assertEqual(CandidateResult.objects.count(), 1)

        # Now reget the original person and her candidacy - check it
        # has a result attached.
        after_merging = Person.objects.get(pk=3885)
        membership = after_merging.memberships.get(
            extra__election=self.election)
        candidate_result = membership.result.get()
        self.assertEqual(candidate_result.num_ballots_reported, 32614)

    def test_uk_results_for_primary_preserved(self):
        primary_membership_extra = factories.CandidacyExtraFactory.create(
            election=self.earlier_election,
            base__person=self.primary_person,
            base__post=self.camberwell_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base,
        )
        factories.CandidacyExtraFactory.create(
            election=self.local_election,
            base__person=self.secondary_person,
            base__post=self.local_post.base,
            base__on_behalf_of=self.labour_party_extra.base,
        )
        factories.CandidacyExtraFactory.create(
            election=self.election,
            base__person=self.secondary_person,
            base__post=self.camberwell_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base,
        )

        # Now attach a vote count to the primary person's candidacy:
        post_result = PostResult.objects.create(
            post=primary_membership_extra.base.post,
            confirmed=False,
        )
        result_set = ResultSet.objects.create(
            post_result=post_result,
            num_turnout_reported=46659,
            num_spoilt_ballots=42,
            ip_address='127.0.0.1',
        )
        CandidateResult.objects.create(
            result_set=result_set,
            membership=primary_membership_extra.base,
            num_ballots_reported=27619,
            is_winner=True,
        )
        # Now try the merge:
        response = self.app.get(
            '/person/3885/update',
            user=self.user_who_can_merge)
        merge_form = response.forms['person-merge']
        merge_form['other'] = '10000'
        response = merge_form.submit()

        self.assertEqual(CandidateResult.objects.count(), 1)

        # Now reget the original person and her candidacy - check it
        # has a result attached.
        after_merging = Person.objects.get(pk=3885)
        membership = after_merging.memberships.get(
            extra__election=self.earlier_election)
        candidate_result = membership.result.get()
        self.assertEqual(candidate_result.num_ballots_reported, 27619)
