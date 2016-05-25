# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import importlib

from django.conf import settings
from django.db import migrations

from mysite.settings.conf import get_conf

def get_election_app_setting(setting_name):
    election_app = settings.ELECTION_APP
    if not election_app:
        return None

    election_app_fully_qualified = 'elections.' + election_app
    election_settings_module = election_app_fully_qualified + '.settings'
    elections_module = importlib.import_module(election_settings_module)
    try:
        setting = getattr(elections_module, setting_name)
    except AttributeError:
        setting = ''

    return setting

def migrate_settings(apps, schema_editor):
    """
    The idea is that this will only run for sites that already have
    settings so they should have a SITE_OWNER and a super user in
    existance. New sites won't have this so we won't try and set
    any of these.
    """
    SiteSettings = apps.get_model('candidates', 'SiteSettings')
    db_alias = schema_editor.connection.alias

    User = apps.get_model('auth', 'User')

    superusers = User.objects.filter(
        is_superuser=True
    ).order_by('date_joined')

    user = superusers.first()

    old_settings = get_conf('general.yml')

    if user and get_election_app_setting('SITE_OWNER'):
        SiteSettings.objects.using(db_alias).create(
            site_id=1,
            user_id=user.id,
            # TODO: check default
            DATE_FORMAT=old_settings.get('DATE_FORMAT', ''),
            SERVER_EMAIL=old_settings['SERVER_EMAIL'],
            DEFAULT_FROM_EMAIL=old_settings['DEFAULT_FROM_EMAIL'],
            SUPPORT_EMAIL=old_settings['SUPPORT_EMAIL'],
            SITE_OWNER=get_election_app_setting('SITE_OWNER'),
            SITE_OWNER_URL=get_election_app_setting('SITE_OWNER_URL'),
            COPYRIGHT_HOLDER=get_election_app_setting('COPYRIGHT_HOLDER'),
            MAPIT_BASE_URL=get_election_app_setting('MAPIT_BASE_URL'),
            IMAGE_PROXY_URL=get_election_app_setting('IMAGE_PROXY_URL'),
            GOOGLE_ANALYTICS_ACCOUNT=old_settings['GOOGLE_ANALYTICS_ACCOUNT'],
            USE_UNIVERSAL_ANALYTICS=old_settings['USE_UNIVERSAL_ANALYTICS'],
            TWITTER_USERNAME=old_settings.get('TWITTER_USERNAME', ''),
            TWITTER_APP_ONLY_BEARER_TOKEN=old_settings.get('TWITTER_APP_ONLY_BEARER_TOKEN', ''),
            RESTRICT_RENAMES=old_settings['RESTRICT_RENAMES'],
            EDITS_ALLOWED=old_settings['EDITS_ALLOWED'],
            HOIST_ELECTED_CANDIDATES=old_settings.get('HOIST_ELECTED_CANDIDATES', True),
            DD_MM_DATE_FORMAT_PREFERRED=old_settings.get('DD_MM_DATE_FORMAT_PREFERRED', True),
            CANDIDATES_REQUIRED_FOR_WEIGHTED_PARTY_LIST=old_settings.get('CANDIDATES_REQUIRED_FOR_WEIGHTED_PARTY_LIST', 20),
        )


# this just here so we can reverse the action
def unmigrate_settings(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0032_sitesettings'),
    ]

    operations = [
        migrations.RunPython(migrate_settings, unmigrate_settings),
    ]
