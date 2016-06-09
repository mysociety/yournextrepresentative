from __future__ import unicode_literals

from django.contrib import admin

from django.core.urlresolvers import reverse
from django.forms import ModelForm

from usersettings.admin import SettingsAdmin

from .models import (
    LoggedAction, PartySet, ExtraField, PersonExtraFieldValue,
    SimplePopoloField, ComplexPopoloField, PostExtraElection,
    SiteSettings
)


class LoggedActionAdminForm(ModelForm):
    pass


@admin.register(LoggedAction)
class LoggedActionAdmin(admin.ModelAdmin):
    form = LoggedActionAdminForm
    search_fields = ('user__username', 'popit_person_new_version',
                     'person__name', 'ip_address', 'source')
    list_filter = ('action_type',)
    list_display = ['user', 'ip_address', 'action_type',
                    'popit_person_new_version', 'person_link',
                    'created', 'updated', 'source', 'note']
    ordering = ('-created',)

    def person_link(self, o):
        if not o.person:
            return ''
        url = reverse('person-view', kwargs={'person_id': o.person.id})
        return '<a href="{0}">{1}</a>'.format(
            url,
            o.person.name,
        )
    person_link.allow_tags = True


class PartySetAdminForm(ModelForm):
    pass


@admin.register(PartySet)
class PartySetAdmin(admin.ModelAdmin):
    form = PartySetAdminForm


class ExtraFieldAdminForm(ModelForm):
    pass


@admin.register(ExtraField)
class ExtraFieldAdmin(admin.ModelAdmin):
    form = ExtraFieldAdminForm


class PersonExtraFieldValueAdminForm(ModelForm):
    pass


@admin.register(PersonExtraFieldValue)
class PersonExtraFieldValueAdmin(admin.ModelAdmin):
    form = PersonExtraFieldValueAdminForm


@admin.register(SimplePopoloField)
class SimplePopoloFieldAdmin(admin.ModelAdmin):
    list_display = ['name', 'label']


@admin.register(PostExtraElection)
class PostExtraElectionAdmin(admin.ModelAdmin):
    list_display = ['postextra', 'election', 'winner_count']
    list_filter = ('election__name', 'election__current')

    ordering = ('election', 'postextra__base__area__name')


@admin.register(ComplexPopoloField)
class ComplexPopoloFieldAdmin(admin.ModelAdmin):
    list_display = ['name', 'label', 'order']
    ordering = ('order',)

@admin.register(SiteSettings)
class SiteSettingsAdmin(SettingsAdmin):
    fieldsets = (
        ("Site owner's details", {
            'fields': ('SITE_OWNER', 'SITE_OWNER_URL', 'COPYRIGHT_HOLDER',
                'TWITTER_USERNAME')
        }),
        ('Email addresses', {
            'fields': ('SUPPORT_EMAIL', 'DEFAULT_FROM_EMAIL', 'SERVER_EMAIL')
        }),
        ('Localization', {
            'fields': ('LANGUAGE', 'DATE_FORMAT', 'DD_MM_DATE_FORMAT_PREFERRED')
        }),
        ('Areas', {
            'fields': ('MAPIT_BASE_URL',)
        }),
        ('Google Analytics', {
            'fields': ('GOOGLE_ANALYTICS_ACCOUNT', 'USE_UNIVERSAL_ANALYTICS')
        }),
        ('Display and editing options', {
            'description': 'How candidates are displayed and if eding is allowed',
            'fields': ('NEW_ACCOUNTS_ALLOWED', 'RESTRICT_RENAMES', 'EDITS_ALLOWED'
                'HOIST_ELECTED_CANDIDATES', 'CANDIDATES_REQUIRED_FOR_WEIGHTED_PARTY_LIST')

        }),
        ('Other', {
            'description': 'How candidates are displayed and if eding is allowed',
            'fields': ('TWITTER_APP_ONLY_BEARER_TOKEN', 'IMAGE_PROXY_URL')
        })
    )
