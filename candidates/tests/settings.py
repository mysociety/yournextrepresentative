from __future__ import unicode_literals

from candidates.models import SiteSettings
from django.contrib.auth.models import User


class SettingsMixin(object):

    def setUp(self):
        super(SettingsMixin, self).setUp()
        self.settings_user = User.objects.create_user(
            'settings',
            'settings' + '@example.com',
            'notagoodpassword',
        )

        self.sitesettings = SiteSettings.objects.create(
            site_id=1,
            user_id=self.settings_user.id,
            SERVER_EMAIL='root@localhost',
            DEFAULT_FROM_EMAIL='webmaster@localhost',
            SUPPORT_EMAIL='yournextmp-support@example.org',
            SITE_OWNER='The Site Owners',
            COPYRIGHT_HOLDER='The Copyright Holders',
            MAPIT_BASE_URL='http://global.mapit.mysociety.org/',
            GOOGLE_ANALYTICS_ACCOUNT='',
            USE_UNIVERSAL_ANALYTICS=True,
            TWITTER_USERNAME='',
            RESTRICT_RENAMES=False,
            EDITS_ALLOWED=True,
            HOIST_ELECTED_CANDIDATES=True,
            DD_MM_DATE_FORMAT_PREFERRED=True,
        )

    def tearDown(self):
        self.sitesettings.delete()
        self.settings_user.delete()
