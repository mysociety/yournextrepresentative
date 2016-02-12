 # -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django_webtest import WebTest

from popolo.models import Person
from .auth import TestUserMixin
from ..models import LoggedAction

class TestFeeds(TestUserMixin, WebTest):

    def setUp(self):
        self.person1 = Person.objects.create(
            name='Test Person1'
        )
        self.person2 = Person.objects.create(
            name='Test Person2'
        )
        self.action1 = LoggedAction.objects.create(
            user=self.user,
            action_type='person-create',
            ip_address='127.0.0.1',
            person=self.person1,
            popit_person_new_version='1234567890abcdef',
            source='Just for tests...',
        )
        self.action2 = LoggedAction.objects.create(
            user=self.user,
            action_type='candidacy-delete',
            ip_address='127.0.0.1',
            person=self.person2,
            popit_person_new_version='987654321',
            source='Something with unicode in it…',
        )

    def test_unicode(self):
        response = self.app.get('/feeds/changes.xml')
        self.assertTrue("Just for tests..." in response)
        self.assertTrue("Something with unicode in it…" in response)

    def tearDown(self):
        self.action2.delete()
        self.action1.delete()
        self.person2.delete()
        self.person1.delete()
