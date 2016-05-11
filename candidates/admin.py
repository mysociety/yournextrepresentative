from __future__ import unicode_literals

from django.contrib import admin

from django.core.urlresolvers import reverse
from django.forms import ModelForm

from .models import (
    LoggedAction, PartySet, ExtraField, PersonExtraFieldValue,
    SimplePopoloField, ComplexPopoloField, PostExtraElection
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
                    'created', 'updated', 'source']
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
    raw_id_fields = ("postextra", "election",)

    ordering = ('election', 'postextra__base__area__name')


@admin.register(ComplexPopoloField)
class ComplexPopoloFieldAdmin(admin.ModelAdmin):
    list_display = ['name', 'label', 'order']
    ordering = ('order',)
