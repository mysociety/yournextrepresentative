from __future__ import unicode_literals

from django_webtest import WebTest

from usersettings.shortcuts import get_current_usersettings

from .auth import TestUserMixin
from .settings import SettingsMixin
from .factories import PersonExtraFactory


class TestEditRestriction(TestUserMixin, SettingsMixin, WebTest):

    def setUp(self):
        super(TestEditRestriction, self).setUp()
        PersonExtraFactory.create(
            base__id=4322,
            base__name='Helen Hayes',
            base__email='hayes@example.com',
        )

    def test_edit_restricted_unprivileged(self):
        settings = get_current_usersettings()
        settings.EDITS_ALLOWED = False
        settings.save()
        response = self.app.get(
            '/person/4322/update',
            user=self.user
        )

        self.assertContains(
            response,
            'Editing of data in  is now disabled'
        )

    def test_edit_restricted_privileged(self):
        settings = get_current_usersettings()
        settings.EDITS_ALLOWED = False
        settings.save()
        response = self.app.get(
            '/person/4322/update',
            user=self.user_is_staff,
        )
        form = response.forms['person-details']
        form['email'] = 'helen@example.com'
        form['source'] = 'Testing renaming'
        submission_response = form.submit(expect_errors=True)
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location,
            'http://localhost:80/person/4322',
        )

    def test_edit_unrestricted_unprivileged(self):
        response = self.app.get(
            '/person/4322/update',
            user=self.user,
        )
        form = response.forms['person-details']
        form['email'] = 'helen@example.com'
        form['source'] = 'Testing renaming'
        submission_response = form.submit(expect_errors=True)
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location,
            'http://localhost:80/person/4322',
        )

    def test_edit_unrestricted_privileged(self):
        response = self.app.get(
            '/person/4322/update',
            user=self.user_is_staff,
        )
        form = response.forms['person-details']
        form['email'] = 'helen@example.com'
        form['source'] = 'Testing renaming'
        submission_response = form.submit(expect_errors=True)
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location,
            'http://localhost:80/person/4322',
        )
