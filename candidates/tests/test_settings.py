# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib.auth.models import User, Group

from usersettings.shortcuts import get_current_usersettings

from django_webtest import WebTest
from django.core.urlresolvers import reverse

from ..models import EDIT_SETTINGS_GROUP_NAME
from ..models import LoggedAction

from .auth import TestUserMixin
from .settings import SettingsMixin


class SettingsTests(TestUserMixin, SettingsMixin, WebTest):

    def setUp(self):
        super(SettingsTests, self).setUp()
        self.test_setter = User.objects.create_superuser(
            'jane',
            'jane@example.com',
            'alsonotagoodpassword',
        )
        self.test_setter.terms_agreement.assigned_to_dc = True
        self.test_setter.terms_agreement.save()
        self.test_setter.groups.add(
            Group.objects.get(name=EDIT_SETTINGS_GROUP_NAME)
        )

    def test_settings_view_unprivileged(self):
        settings_url = reverse(
            'settings',
        )
        response = self.app.get(
            settings_url,
            user=self.user,
            expect_errors=True
        )
        self.assertEqual(response.status_code, 403)

    def test_settings_view_privileged(self):
        settings_url = reverse(
            'settings',
        )
        response = self.app.get(settings_url, user=self.test_setter)
        self.assertEqual(response.status_code, 200)

    def test_settings_loaded(self):
        settings_url = reverse(
            'settings',
        )
        response = self.app.get(settings_url, user=self.test_setter)
        form = response.forms['settings']

        # just check a sample
        self.assertEqual(form['SITE_OWNER'].value, 'The Site Owners')
        self.assertEqual(form['SERVER_EMAIL'].value, 'root@localhost')

    def test_settings_saved(self):
        settings_url = reverse(
            'settings',
        )
        response = self.app.get(settings_url, user=self.test_setter)
        form = response.forms['settings']

        form['SITE_OWNER'].value = 'The New Owners'
        response = form.submit()

        self.assertEqual(form['SITE_OWNER'].value, 'The New Owners')

        settings = get_current_usersettings()
        self.assertEqual(settings.SITE_OWNER, 'The New Owners')

    def test_logged_action_created(self):
        settings_url = reverse(
            'settings',
        )
        response = self.app.get(settings_url, user=self.test_setter)
        form = response.forms['settings']

        form['SITE_OWNER'].value = 'The New Owners'
        response = form.submit()

        settings = get_current_usersettings()
        self.assertEqual(settings.SITE_OWNER, 'The New Owners')

        actions = LoggedAction.objects.filter(
            action_type='settings-edited'
        ).order_by('-created')

        action = actions[0]

        self.assertEqual(
            action.note,
            "Changed SITE_OWNER from \"The Site Owners\" to \"The New Owners\"\n"
        )
