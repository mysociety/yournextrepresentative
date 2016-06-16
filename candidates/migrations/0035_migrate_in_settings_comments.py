# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0034_add_can_edit_settings_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitesettings',
            name='CANDIDATES_REQUIRED_FOR_WEIGHTED_PARTY_LIST',
            field=models.IntegerField(verbose_name='Number of candidates required for weighted party list', help_text='If there are more than this number of candidates (either in current\nelections or all elections) for a particular party set we use a\n"weighted" party list - i.e. the party drop-down is ordered from the\nparty in the party set with most candidates down to those with the\nleast.\n', default=20),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='COPYRIGHT_HOLDER',
            field=models.CharField(max_length=250, verbose_name='Copyright holder'),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='DATE_FORMAT',
            field=models.CharField(max_length=250, verbose_name='Date format', blank=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='DD_MM_DATE_FORMAT_PREFERRED',
            field=models.BooleanField(help_text="'In all of the world apart from the United States, dd/mm is preferred\nto mm/dd.  So if your site is for the USA, set this to false.\n", verbose_name='Expect day to come before month in numeric dates (e.g. dd/mm/yyyy)', default=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='DEFAULT_FROM_EMAIL',
            field=models.EmailField(max_length=250, verbose_name="'From' email address to use in emails sent by the site", help_text="The 'From' address for all emails except error emails."),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='EDITS_ALLOWED',
            field=models.BooleanField(help_text='If this is set to false, then no edits of candidates are allowed.', verbose_name='Allow candidates to be edited', default=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='GOOGLE_ANALYTICS_ACCOUNT',
            field=models.CharField(help_text='You can use Google Analytics by changing this to your Google\nAnalytics tracking ID.\n', max_length=250, verbose_name='Google Analytics account ID', blank=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='HOIST_ELECTED_CANDIDATES',
            field=models.BooleanField(help_text="When candidates are marked as being elected, they're shown in a\nspecial 'elected' section on post and area pages.  If this option is\nfalse, they will shown both in that elected section and a complete\nlist of candidates below.  If it is true, then it's as if the\nelected candidates have been hoisted up to the elected section.\n", verbose_name='Only display elected candidates at top of page', default=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='MAPIT_BASE_URL',
            field=models.URLField(max_length=250, verbose_name='MapIt base URL', blank=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='NEW_ACCOUNTS_ALLOWED',
            field=models.BooleanField(help_text='If this is set to false, then no new accounts may be created - you\nmight want this past a certain point in the election to reduce\nopportunities for "drive-by" malicious edits.\n', verbose_name='Allow new accounts to be created', default=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='RESTRICT_RENAMES',
            field=models.BooleanField(help_text="If this is true, you have to be in the 'Trusted to Rename' group in\norder to change the name of a candidate:\n", verbose_name='Restrict users from changing candidate names', default=False),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='SERVER_EMAIL',
            field=models.EmailField(max_length=250, verbose_name="'From' email address to use in error emails"),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='SITE_OWNER',
            field=models.CharField(max_length=250, verbose_name='Site owner'),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='SITE_OWNER_URL',
            field=models.URLField(max_length=250, verbose_name='Website for site owner', blank=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='SUPPORT_EMAIL',
            field=models.EmailField(max_length=250, verbose_name='Email address for support enquiries to be sent to', help_text='The email address that will be displayed on the site as the contact\nemail for all support requests, and so on.\n'),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='TWITTER_APP_ONLY_BEARER_TOKEN',
            field=models.CharField(help_text='Twitter application-only bearer token.  This is important so that\n(a) Twitter usernames can be validated as actually existing when\nthey\'re supplied by a user (b) the stable Twitter user ID is stored\nwhen someone sets a Twitter username and (c) the\ncandidates_update_twitter_usernames command (which deals with\nchanges of screen name) will work.\n\nYou can generate an application-only bearer token with:\n\n  curl -u "$CONSUMER_KEY:$CONSUMER_SECRET"        --data \'grant_type=client_credentials\'        \'https://api.twitter.com/oauth2/token\'\n\nOr see https://dev.twitter.com/oauth/application-only for more\ndetails.\n', max_length=250, verbose_name='Twitter API bearer token', blank=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='TWITTER_USERNAME',
            field=models.CharField(help_text="You should set this to the name of a Twitter account associated with\nthe site; this will be used in the Twitter metadata for various\npages. This should just be the name of that account (not a URL), and\nshouldn't include the @.\n", max_length=250, verbose_name='Twitter username', blank=True),
        ),
        migrations.AlterField(
            model_name='sitesettings',
            name='USE_UNIVERSAL_ANALYTICS',
            field=models.BooleanField(help_text="This should be set to true unless you're using the old version of\nGoogle Analytics.\n", verbose_name='Use Universal Google Analytics', default=True),
        ),
    ]
