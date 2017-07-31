# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from usersettings.shortcuts import get_current_usersettings

from allauth.socialaccount.models import SocialApp
from django_webtest import WebTest
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

from .settings import SettingsMixin

class SettingsTests(SettingsMixin, WebTest):

    def setUp(self):
        super(SettingsTests, self).setUp()
        social_account = SocialApp.objects.create(
            provider='facebook',
            name='Fake Facebook SocialAccount',
            client_id='abcdefghijklm',
            secret='AAAAAAAAAAAAAAAA',
        )
        site = Site.objects.get()
        social_account.sites.add(site)

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
