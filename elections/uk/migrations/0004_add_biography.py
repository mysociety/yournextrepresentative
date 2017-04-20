# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    def create_simple_fields(apps, schema_editor):
        SimpleField = apps.get_model('candidates', 'SimplePopoloField')
        db_alias = schema_editor.connection.alias

        SimpleField.objects.using(db_alias).create(
            name='biography',
            label='Biography',
            required=False,
            info_type_key='text_multiline',
            order=10,
        )


    dependencies = [
        ('uk', '0003_adjust_roles_for_grouping'),
    ]

    operations = [
        migrations.RunPython(create_simple_fields),
    ]
