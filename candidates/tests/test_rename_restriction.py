from __future__ import unicode_literals

from django_webtest import WebTest

from usersettings.shortcuts import get_current_usersettings

from .auth import TestUserMixin
from .settings import SettingsMixin
from .factories import PersonExtraFactory

# FIXME: these pass individually but fail together because of
# https://github.com/django-compressor/django-appconf/issues/30

class TestRenameRestriction(TestUserMixin, SettingsMixin, WebTest):

    def setUp(self):
        super(TestRenameRestriction, self).setUp()
        PersonExtraFactory.create(
            base__id=4322,
            base__name='Helen Hayes',
            base__email='hayes@example.com',
        )

    def test_renames_restricted_unprivileged(self):
        settings = get_current_usersettings()
        settings.RESTRICT_RENAMES = True
        settings.save()
        response = self.app.get(
            '/person/4322/update',
            user=self.user
        )
        form = response.forms['person-details']
        form['name'] = 'Ms Helen Hayes'
        form['source'] = 'Testing renaming'
        submission_response = form.submit(expect_errors=True)
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location,
            'http://localhost:80/update-disallowed',
        )

    def test_renames_restricted_privileged(self):
        settings = get_current_usersettings()
        settings.RESTRICT_RENAMES = True
        settings.save()
        response = self.app.get(
            '/person/4322/update',
            user=self.user_who_can_rename,
        )
        form = response.forms['person-details']
        form['name'] = 'Ms Helen Hayes'
        form['source'] = 'Testing renaming'
        submission_response = form.submit(expect_errors=True)
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location,
            'http://localhost:80/person/4322',
        )

    def test_renames_unrestricted_unprivileged(self):
        response = self.app.get(
            '/person/4322/update',
            user=self.user,
        )
        form = response.forms['person-details']
        form['name'] = 'Ms Helen Hayes'
        form['source'] = 'Testing renaming'
        submission_response = form.submit(expect_errors=True)
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location,
            'http://localhost:80/person/4322',
        )

    def test_renames_unrestricted_privileged(self):
        response = self.app.get(
            '/person/4322/update',
            user=self.user,
        )
        form = response.forms['person-details']
        form['name'] = 'Ms Helen Hayes'
        form['source'] = 'Testing renaming'
        submission_response = form.submit(expect_errors=True)
        self.assertEqual(submission_response.status_code, 302)
        self.assertEqual(
            submission_response.location,
            'http://localhost:80/person/4322',
        )
