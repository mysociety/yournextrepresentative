import json

from django.core.management import call_command
from django_webtest import WebTest
from popolo.models import Membership, Person

from candidates.tests.test_update_view import membership_id_set
from candidates.tests.auth import TestUserMixin

from official_documents.models import OfficialDocument

from nose.plugins.attrib import attr
from candidates.tests import factories
from candidates.tests.uk_examples import UK2015ExamplesMixin


@attr(country='uk')
class TestBulkAdding(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestBulkAdding, self).setUp()
        call_command('rebuild_index', verbosity=0, interactive=False)

    def testNoFormIfNoSopn(self):
        response = self.app.get(
            '/bulk_adding/2015/65808/',
            user=self.user_who_can_upload_documents
        )

        self.assertContains(
            response,
            "This post doesn't have a nomination paper"
        )

        self.assertNotContains(
            response,
            "Review"
        )

    def testFormIfSopn(self):
        post = self.dulwich_post_extra

        doc = OfficialDocument.objects.create(
            election=self.election,
            post=post.base,
            source_url='http://example.com',
            document_type=OfficialDocument.NOMINATION_PAPER,
            uploaded_file="sopn.pdf"
        )

        response = self.app.get(
            '/bulk_adding/2015/65808/',
            user=self.user_who_can_upload_documents
        )

        self.assertNotContains(
            response,
            "This post doesn't have a nomination paper"
        )

        self.assertContains(
            response,
            "Review"
        )

    def test_submitting_form(self):
        post = self.dulwich_post_extra.base

        OfficialDocument.objects.create(
            election=self.election,
            post=post,
            source_url='http://example.com',
            document_type=OfficialDocument.NOMINATION_PAPER,
            uploaded_file="sopn.pdf"
        )

        response = self.app.get(
            '/bulk_adding/2015/65808/',
            user=self.user
        )

        form = response.forms['bulk_add_form']
        form['form-0-name'] = 'Homer Simpson'
        form['form-0-party'] = self.green_party_extra.base.id

        response = form.submit()
        self.assertEqual(response.status_code, 302)

        # This takes us to a page with a radio button for adding them
        # as a new person or alternative radio buttons if any
        # candidates with similar names were found.
        response = response.follow()
        form = response.forms[1]
        form['form-0-select_person'].select('_new')
        response = form.submit()

        self.assertEqual(Person.objects.count(), 1)
        homer = Person.objects.get()
        self.assertEqual(homer.name, 'Homer Simpson')
        homer_versions = json.loads(homer.extra.versions)
        self.assertEqual(len(homer_versions), 2)
        self.assertEqual(
            homer_versions[0]['information_source'],
            'http://example.com')
        self.assertEqual(
            homer_versions[1]['information_source'],
            'http://example.com')

        self.assertEqual(homer.memberships.count(), 1)
        membership = homer.memberships.get()
        self.assertEqual(membership.role, 'Candidate')
        self.assertEqual(membership.on_behalf_of.name, 'Green Party')
        self.assertEqual(
            membership.post.label,
            'Member of Parliament for Dulwich and West Norwood')

    def test_adding_to_existing_person(self):
        existing_person = factories.PersonExtraFactory.create(
            base__id='1234567',
            base__name='Bart Simpson'
        ).base
        existing_membership = factories.CandidacyExtraFactory.create(
            election=self.local_election,
            base__person=existing_person,
            base__post=self.local_post.base,
            base__on_behalf_of=self.labour_party_extra.base
        ).base
        memberships_before = membership_id_set(existing_person)
        # Now try adding that person via bulk add:
        OfficialDocument.objects.create(
            election=self.election,
            post=self.dulwich_post_extra.base,
            source_url='http://example.com',
            document_type=OfficialDocument.NOMINATION_PAPER,
            uploaded_file="sopn.pdf"
        )

        response = self.app.get(
            '/bulk_adding/2015/65808/',
            user=self.user
        )

        form = response.forms['bulk_add_form']
        form['form-0-name'] = 'Bart Simpson'
        form['form-0-party'] = self.green_party_extra.base.id

        response = form.submit()
        self.assertEqual(response.status_code, 302)

        # This takes us to a page with a radio button for adding them
        # as a new person or alternative radio buttons if any
        # candidates with similar names were found.
        response = response.follow()
        form = response.forms[1]
        form['form-0-select_person'].select('1234567')
        response = form.submit()

        person = Person.objects.get(name='Bart Simpson')
        memberships_after = membership_id_set(person)
        new_memberships = memberships_after - memberships_before
        self.assertEqual(len(new_memberships), 1)
        new_membership = Membership.objects.get(pk=list(new_memberships)[0])
        self.assertEqual(new_membership.post, self.dulwich_post_extra.base)
        self.assertEqual(new_membership.on_behalf_of, self.green_party_extra.base)
        same_memberships = memberships_before & memberships_after
        self.assertEqual(len(same_memberships), 1)
        same_membership = Membership.objects.get(pk=list(same_memberships)[0])
        self.assertEqual(same_membership.post, self.local_post.base)
        self.assertEqual(same_membership.on_behalf_of, self.labour_party_extra.base)
        self.assertEqual(same_membership.id, existing_membership.id)

    def test_adding_to_existing_person_same_election(self):
        # This could happen if someone's missed that there was the
        # same person already listed on the first page, but then
        # spotted them on the review page and said to merge them then.
        existing_person = factories.PersonExtraFactory.create(
            base__id='1234567',
            base__name='Bart Simpson'
        ).base
        existing_membership = factories.CandidacyExtraFactory.create(
            election=self.election,
            base__person=existing_person,
            # !!! This is the line that differs from the previous test:
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base
        ).base
        memberships_before = membership_id_set(existing_person)
        # Now try adding that person via bulk add:
        OfficialDocument.objects.create(
            election=self.election,
            post=self.dulwich_post_extra.base,
            source_url='http://example.com',
            document_type=OfficialDocument.NOMINATION_PAPER,
            uploaded_file="sopn.pdf"
        )

        response = self.app.get(
            '/bulk_adding/2015/65808/',
            user=self.user
        )

        form = response.forms['bulk_add_form']
        form['form-0-name'] = 'Bart Simpson'
        form['form-0-party'] = self.green_party_extra.base.id

        response = form.submit()
        self.assertEqual(response.status_code, 302)

        # This takes us to a page with a radio button for adding them
        # as a new person or alternative radio buttons if any
        # candidates with similar names were found.
        response = response.follow()
        form = response.forms[1]
        form['form-0-select_person'].select('1234567')
        response = form.submit()

        person = Person.objects.get(name='Bart Simpson')
        memberships_after = membership_id_set(person)
        new_memberships = memberships_after - memberships_before
        self.assertEqual(len(new_memberships), 0)
        same_memberships = memberships_before & memberships_after
        self.assertEqual(len(same_memberships), 1)
        same_membership = Membership.objects.get(pk=list(same_memberships)[0])
        self.assertEqual(same_membership.post, self.dulwich_post_extra.base)
        self.assertEqual(same_membership.on_behalf_of, self.green_party_extra.base)
        self.assertEqual(same_membership.id, existing_membership.id)
