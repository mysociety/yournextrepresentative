# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0027_create_standard_complex_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='complexpopolofield',
            name='info_type_key',
            field=models.CharField(help_text="Name of the field in the array that stores the type ('note' for links, 'contact_type' for contacts, 'scheme' for identifiers)", max_length=100),
        ),
        migrations.AlterField(
            model_name='complexpopolofield',
            name='info_value_key',
            field=models.CharField(help_text="Name of the field in the array that stores the value, e.g 'url' for links, 'value' for contact_type, 'identifier' for identifiers", max_length=100),
        ),
        migrations.AlterField(
            model_name='complexpopolofield',
            name='old_info_type',
            field=models.CharField(help_text="Used for supporting info_types that have been renamed. As such it's rarely used.", max_length=100, blank=True),
        ),
    ]
