from __future__ import unicode_literals, print_function

from mock import patch

from django.test import TestCase
from popolo.models import Membership, Post

from elections.models import Election

from ..models import (
    MembershipExtra, PostExtra,
    check_paired_models, check_membership_elections_consistent)
from .factories import (
    ElectionFactory, MembershipExtraFactory, PersonExtraFactory)
from .uk_examples import UK2015ExamplesMixin


class PairedConstraintCheckTests(UK2015ExamplesMixin, TestCase):

    def test_no_problems_normally(self):
        errors = check_paired_models()
        for e in errors:
            print(e)
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


class PostElectionCombinationTests(UK2015ExamplesMixin, TestCase):

    def test_relationship_ok(self):
        new_candidate = PersonExtraFactory.create(
            base__name='John Doe'
        )
        post_extra = PostExtra.objects.get(slug='14419')
        election = Election.objects.get(slug='2015')
        # Create a new candidacy:
        MembershipExtraFactory.create(
            base__person=new_candidate.base,
            base__post=post_extra.base,
            base__organization=election.organization,
            election=election,
        )
        self.assertEqual(
            check_membership_elections_consistent(),
            [])

    def test_membership_extra_not_in_post_election_extra(self):
        new_candidate = PersonExtraFactory.create(
            base__name='John Doe'
        )
        post_extra = PostExtra.objects.get(slug='14419')
        election = ElectionFactory.create(
            slug='2005',
            name='2005 General Election',
            for_post_role='Member of Parliament',
            area_types=(self.wmc_area_type,)
        )
        # Create a broken candidacy, where the post / election
        # combination isn't represented in PostExtraElection
        # relationships. (In order to create this bad data for the
        # test, we add an attribute to the MembershipExtra class to
        # tell the save method not to try preventing creation of the
        # bad data.)
        with patch.object(
                MembershipExtra, 'check_for_broken', False, create=True):
            MembershipExtraFactory.create(
                base__person=new_candidate.base,
                base__post=post_extra.base,
                base__organization=election.organization,
                election=election,
            )
        expected_error = "There was a membership for John Doe ({0}) with " \
            "post Member of Parliament for Edinburgh East (14419) and " \
            "election 2005 but there's no PostExtraElection linking " \
            "them.".format(new_candidate.base.id)
        self.assertEqual(
            check_membership_elections_consistent(),
            [expected_error])


class PreventCreatingBadMembershipExtras(UK2015ExamplesMixin, TestCase):

    def test_prevent_creating(self):
        new_candidate = PersonExtraFactory.create(
            base__name='John Doe'
        )
        post_extra = PostExtra.objects.get(slug='14419')
        election = ElectionFactory.create(
            slug='2005',
            name='2005 General Election',
            for_post_role='Member of Parliament',
            area_types=(self.wmc_area_type,)
        )
        membership = Membership.objects.create(
            role='Candidate',
            person=new_candidate.base,
            on_behalf_of=self.green_party_extra.base,
            post=post_extra.base,
        )
        with self.assertRaisesRegexp(
                Exception,
                r'Trying to create a candidacy for post Member of Parliament ' \
                'for Edinburgh East and election 2005 General Election that ' \
                'aren\'t linked'):
            MembershipExtra.objects.create(
                base=membership,
                election=election)
