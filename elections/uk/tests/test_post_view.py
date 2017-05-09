from __future__ import unicode_literals

from django_webtest import WebTest

from moderation_queue.models import SuggestedPostLock
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

    def test_create_suggested_post_lock(self):
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
        form = response.forms['suggest_lock_form']
        form['justification'] = 'I liked totally reviewed the SOPN'
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.location,
            'http://localhost:80/election/2015/post/14419/edinburgh-east')

        suggested_locks = SuggestedPostLock.objects.all()
        self.assertEqual(suggested_locks.count(), 1)
        suggested_lock = suggested_locks.get()
        self.assertEqual(suggested_lock.postextraelection.postextra.slug, '14419')
        self.assertEqual(suggested_lock.postextraelection.election.slug, '2015')
        self.assertEqual(suggested_lock.user, self.user)
        self.assertEqual(suggested_lock.justification, 'I liked totally reviewed the SOPN')
