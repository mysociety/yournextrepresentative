# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('candidates', '0031_loggedaction_note'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Last Updated')),
                ('DATE_FORMAT', models.CharField(max_length=250, verbose_name='Date Format', blank=True)),
                ('SERVER_EMAIL', models.EmailField(max_length=250, verbose_name='From address for error emails')),
                ('DEFAULT_FROM_EMAIL', models.EmailField(max_length=250, verbose_name='Default From email address')),
                ('SUPPORT_EMAIL', models.EmailField(max_length=250, verbose_name='Support Email')),
                ('SITE_OWNER', models.CharField(max_length=250, verbose_name='Site Owner')),
                ('SITE_OWNER_URL', models.URLField(max_length=250, verbose_name='Website for Site Owner', blank=True)),
                ('COPYRIGHT_HOLDER', models.CharField(max_length=250, verbose_name='Copyright Holder')),
                ('MAPIT_BASE_URL', models.URLField(max_length=250, verbose_name='Mapit base URL', blank=True)),
                ('IMAGE_PROXY_URL', models.URLField(max_length=250, verbose_name='Image proxy URL', blank=True)),
                ('GOOGLE_ANALYTICS_ACCOUNT', models.CharField(max_length=250, verbose_name='Google Analytics Account ID', blank=True)),
                ('USE_UNIVERSAL_ANALYTICS', models.BooleanField(default=True, verbose_name='Using Universal Google analytics')),
                ('TWITTER_USERNAME', models.CharField(max_length=250, verbose_name='Twitter username', blank=True)),
                ('TWITTER_APP_ONLY_BEARER_TOKEN', models.CharField(max_length=250, verbose_name='Twitter API bearer token', blank=True)),
                ('RESTRICT_RENAMES', models.BooleanField(default=False, verbose_name='Restrict Renames')),
                ('NEW_ACCOUNTS_ALLOWED', models.BooleanField(default=True, verbose_name='Allow new accounts')),
                ('EDITS_ALLOWED', models.BooleanField(default=True, verbose_name='Allow edits')),
                ('HOIST_ELECTED_CANDIDATES', models.BooleanField(default=True, verbose_name='Hoist elected Candidated')),
                ('DD_MM_DATE_FORMAT_PREFERRED', models.BooleanField(default=True, verbose_name='Prefer DD/MM date format')),
                ('CANDIDATES_REQUIRED_FOR_WEIGHTED_PARTY_LIST', models.IntegerField(default=20, verbose_name='Maximum party list size to display on post page')),
                ('site', models.OneToOneField(related_name='usersettings', null=True, editable=False, to='sites.Site')),
                ('user', models.ForeignKey(related_name='usersettings', editable=False, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Site Settings',
                'verbose_name_plural': 'Site Settings',
            },
        ),
    ]
