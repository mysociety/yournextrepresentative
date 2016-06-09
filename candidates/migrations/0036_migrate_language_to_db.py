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
        settings = SiteSettings.objects.using(db_alias).filter(
            site_id=1,
        ).first()

        settings.LANGUAGE = old_settings.LANGUAGE_CODE


# this just here so we can reverse the action
def unmigrate_settings(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0035_add_language_to_settings'),
    ]

    operations = [
        migrations.RunPython(migrate_settings, unmigrate_settings),
    ]
