# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from usersettings.shortcuts import get_current_usersettings

from django_webtest import WebTest
from django.core.urlresolvers import reverse

from .settings import SettingsMixin


class SettingsTests(SettingsMixin, WebTest):

    def test_signup_allowed(self):
        settings_url = reverse(
            'account_signup',
        )
        response = self.app.get(
            settings_url,
            expect_errors=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password (again)')
        self.assertNotContains(response, 'Sign Up Closed')

    def test_signup_disabled(self):
        user_settings = get_current_usersettings()
        user_settings.NEW_ACCOUNTS_ALLOWED = False;
        user_settings.save()
        settings_url = reverse(
            'account_signup',
        )
        response = self.app.get(
            settings_url,
            expect_errors=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign Up Closed')
        self.assertNotContains(response, 'Password (again)')
