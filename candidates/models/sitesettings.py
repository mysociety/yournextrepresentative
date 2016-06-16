from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from usersettings.models import UserSettings


class SiteSettings(UserSettings):
    # TODO: is this actually used anywhere?
    DATE_FORMAT = models.CharField(
        _('Date format'),
        max_length=250,
        blank=True
    )
    SERVER_EMAIL = models.EmailField(
        _("'From' email address to use in error emails"),
        max_length=250,
    )
    DEFAULT_FROM_EMAIL = models.EmailField(
        _("'From' email address to use in emails sent by the site"),
        max_length=250,
        help_text=_("The 'From' address for all emails except error emails.")
    )
    SUPPORT_EMAIL = models.EmailField(
        _('Email address for support enquiries to be sent to'),
        max_length=250,
        help_text=_(
            '''\
The email address that will be displayed on the site as the contact
email for all support requests, and so on.
'''
        )
    )
    SITE_OWNER = models.CharField(
        _('Site owner'),
        max_length=250,
    )
    SITE_OWNER_URL = models.URLField(
        _('Website for site owner'),
        max_length=250,
        blank=True,
    )
    COPYRIGHT_HOLDER = models.CharField(
        _('Copyright holder'),
        max_length=250,
    )
    MAPIT_BASE_URL = models.URLField(
        _('MapIt base URL'),
        max_length=250,
        blank=True
    )
    IMAGE_PROXY_URL = models.URLField(
        _('Image proxy URL'),
        max_length=250,
        blank=True
    )
    GOOGLE_ANALYTICS_ACCOUNT = models.CharField(
        _('Google Analytics account ID'),
        max_length=250,
        blank=True,
        help_text=_(
            '''\
You can use Google Analytics by changing this to your Google
Analytics tracking ID.
'''
        )
    )
    USE_UNIVERSAL_ANALYTICS = models.BooleanField(
        _('Use Universal Google Analytics'),
        default=True,
        help_text=_(
            '''\
This should be set to true unless you're using the old version of
Google Analytics.
'''
        )
    )
    TWITTER_USERNAME = models.CharField(
        _('Twitter username'),
        max_length=250,
        blank=True,
        help_text=_(
            '''\
You should set this to the name of a Twitter account associated with
the site; this will be used in the Twitter metadata for various
pages. This should just be the name of that account (not a URL), and
shouldn't include the @.
'''
        )
    )
    TWITTER_APP_ONLY_BEARER_TOKEN = models.CharField(
        _('Twitter API bearer token'),
        max_length=250,
        blank=True,
        help_text=_(
            '''\
Twitter application-only bearer token.  This is important so that
(a) Twitter usernames can be validated as actually existing when
they're supplied by a user (b) the stable Twitter user ID is stored
when someone sets a Twitter username and (c) the
candidates_update_twitter_usernames command (which deals with
changes of screen name) will work.

You can generate an application-only bearer token with:

  curl -u "$CONSUMER_KEY:$CONSUMER_SECRET" \
       --data 'grant_type=client_credentials' \
       'https://api.twitter.com/oauth2/token'

Or see https://dev.twitter.com/oauth/application-only for more
details.
'''
        )
    )
    RESTRICT_RENAMES = models.BooleanField(
        _('Restrict users from changing candidate names'),
        default=False,
        help_text=_(
            '''\
If this is true, you have to be in the 'Trusted to Rename' group in
order to change the name of a candidate:
'''
        )
    )
    NEW_ACCOUNTS_ALLOWED = models.BooleanField(
        _('Allow new accounts to be created'),
        default=True,
        help_text=_(
            '''\
If this is set to false, then no new accounts may be created - you
might want this past a certain point in the election to reduce
opportunities for "drive-by" malicious edits.
'''
        )
    )
    EDITS_ALLOWED = models.BooleanField(
        _('Allow candidates to be edited'),
        default=True,
        help_text=_(
            'If this is set to false, then no edits of candidates are allowed.'
        )
    )
    HOIST_ELECTED_CANDIDATES = models.BooleanField(
        _('Only display elected candidates at top of page'),
        default=True,
        help_text=_(
            '''\
When candidates are marked as being elected, they're shown in a
special 'elected' section on post and area pages.  If this option is
false, they will shown both in that elected section and a complete
list of candidates below.  If it is true, then it's as if the
elected candidates have been hoisted up to the elected section.
'''
        )
    )
    DD_MM_DATE_FORMAT_PREFERRED = models.BooleanField(
        _('Expect day to come before month in numeric dates (e.g. dd/mm/yyyy)'),
        default=True,
        help_text=_(
            ''''\
In all of the world apart from the United States, dd/mm is preferred
to mm/dd.  So if your site is for the USA, set this to false.
'''
        )
    )
    CANDIDATES_REQUIRED_FOR_WEIGHTED_PARTY_LIST = models.IntegerField(
        _('Number of candidates required for weighted party list'),
        default=20,
        help_text=_(
            '''\
If there are more than this number of candidates (either in current
elections or all elections) for a particular party set we use a
"weighted" party list - i.e. the party drop-down is ordered from the
party in the party set with most candidates down to those with the
least.
'''
        )
    )

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
