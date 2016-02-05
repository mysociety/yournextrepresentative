# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations


def add_extra_field(apps, schema_editor):
    ExtraField = apps.get_model('candidates', 'ExtraField')
    if settings.ELECTION_APP == 'cr':
         ExtraField.objects.create(
            key='reelection',
            type='yesno',
            label='Standing for re-election',
        )


def remove_extra_field(apps, schema_editor):
    ExtraField = apps.get_model('candidates', 'ExtraField')
    if settings.ELECTION_APP == 'cr':
        extra_field = ExtraField.objects.get('reelection')
        extra_field.personextrafieldvalue_set.all().delete()
        extra_field.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0019_add_yesno_to_extra_field_types'),
    ]

    operations = [
        migrations.RunPython(add_extra_field, remove_extra_field)
    ]
