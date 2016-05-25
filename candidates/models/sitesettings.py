from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from usersettings.models import UserSettings


class SiteSettings(UserSettings):
    # TODO: is this actually used anywhere?
    DATE_FORMAT = models.CharField(
        _('Date Format'),
        max_length=250,
        blank=True
    )
    SERVER_EMAIL = models.EmailField(
        _('From address for error emails'),
        max_length=250,
    )
    DEFAULT_FROM_EMAIL = models.EmailField(
        _('Default From email address'),
        max_length=250,
    )
    SUPPORT_EMAIL = models.EmailField(
        _('Support Email'),
        max_length=250,
    )
    SITE_OWNER = models.CharField(
        _('Site Owner'),
        max_length=250,
    )
    SITE_OWNER_URL = models.URLField(
        _('Website for Site Owner'),
        max_length=250,
        blank=True,
    )
    COPYRIGHT_HOLDER = models.CharField(
        _('Copyright Holder'),
        max_length=250,
    )
    MAPIT_BASE_URL = models.URLField(
        _('MapIt base URL'),
        max_length=250,
        blank=True
    )
    IMAGE_PROXY_URL = models.URLField(
        _('Image Proxy URL'),
        max_length=250,
        blank=True
    )
    GOOGLE_ANALYTICS_ACCOUNT = models.CharField(
        _('Google Analytics Account ID'),
        max_length=250,
        blank=True
    )
    USE_UNIVERSAL_ANALYTICS = models.BooleanField(
        _('Using Universal Google analytics'),
        default=True
    )
    TWITTER_USERNAME = models.CharField(
        _('Twitter username'),
        max_length=250,
        blank=True
    )
    TWITTER_APP_ONLY_BEARER_TOKEN = models.CharField(
        _('Twitter API bearer token'),
        max_length=250,
        blank=True
    )
    RESTRICT_RENAMES = models.BooleanField(
        _('Restrict Renames'),
        default=False
    )
    NEW_ACCOUNTS_ALLOWED = models.BooleanField(
        _('Allow new accounts'),
        default=True
    )
    EDITS_ALLOWED = models.BooleanField(
        _('Allow edits'),
        default=True
    )
    HOIST_ELECTED_CANDIDATES = models.BooleanField(
        _('Hoist elected Candidated'),
        default=True
    )
    DD_MM_DATE_FORMAT_PREFERRED = models.BooleanField(
        _('Prefer DD/MM date format'),
        default=True
    )
    CANDIDATES_REQUIRED_FOR_WEIGHTED_PARTY_LIST = models.IntegerField(
        _('Maximum party list size to display on post page'),
        default=20
    )

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
