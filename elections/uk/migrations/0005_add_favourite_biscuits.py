# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    def create_simple_fields(apps, schema_editor):
        ExtraField = apps.get_model('candidates', 'ExtraField')
        db_alias = schema_editor.connection.alias

        ExtraField.objects.using(db_alias).update_or_create(
            key='favourite_biscuits',
            defaults={
                'label': 'Favourite biscuit 🍪',
                'type': 'line',
                'order': 1,
            }
        )


    dependencies = [
        ('uk', '0004_add_biography'),
    ]

    operations = [
        migrations.RunPython(create_simple_fields),
    ]
