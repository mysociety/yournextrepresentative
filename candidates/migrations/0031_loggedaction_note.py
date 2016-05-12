# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0030_update_complexfields_help_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='loggedaction',
            name='note',
            field=models.TextField(null=True, blank=True),
        ),
    ]
