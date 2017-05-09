from __future__ import unicode_literals

from django_webtest import WebTest

from official_documents.models import OfficialDocument

from nose.plugins.attrib import attr

from candidates.models import PostExtraElection
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin


@attr(country='uk')
class TestConstituencyDetailView(TestUserMixin, UK2015ExamplesMixin, WebTest):

    def test_suggest_post_lock_offered_with_document_when_unlocked(self):
        OfficialDocument.objects.create(
            election=self.election,
            post=self.edinburgh_east_post_extra.base,
            source_url='http://example.com',
            document_type=OfficialDocument.NOMINATION_PAPER,
            uploaded_file="sopn.pdf"
        )
        response = self.app.get(
            '/election/2015/post/14419/edinburgh-east',
            user=self.user,
        )
        self.assertIn('suggest_lock_form', response.forms)

    def test_suggest_post_lock_not_offered_without_document_when_unlocked(self):
        response = self.app.get(
            '/election/2015/post/14419/edinburgh-east',
            user=self.user,
        )
        self.assertNotIn('suggest_lock_form', response.forms)
        
    def test_suggest_post_lock_not_offered_with_document_when_locked(self):
        pee = PostExtraElection.objects.get(
            election__slug='2015',
            postextra__slug='14419',
        )
        pee.candidates_locked = True
        pee.save()
        OfficialDocument.objects.create(
            election=self.election,
            post=self.edinburgh_east_post_extra.base,
            source_url='http://example.com',
            document_type=OfficialDocument.NOMINATION_PAPER,
            uploaded_file="sopn.pdf"
        )
        response = self.app.get(
            '/election/2015/post/14419/edinburgh-east',
            user=self.user,
        )
        self.assertNotIn('suggest_lock_form', response.forms)
