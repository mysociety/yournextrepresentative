from django_webtest import WebTest
from candidates.tests.auth import TestUserMixin

from official_documents.models import OfficialDocument

from nose.plugins.attrib import attr
from candidates.tests.uk_examples import UK2015ExamplesMixin


@attr(country='uk')
class TestBulkAdding(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def setUp(self):
        super(TestBulkAdding, self).setUp()

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
