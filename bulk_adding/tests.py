import json

from django.core.management import call_command
from django_webtest import WebTest
from popolo.models import Person

from candidates.tests.auth import TestUserMixin

from official_documents.models import OfficialDocument

from nose.plugins.attrib import attr
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
