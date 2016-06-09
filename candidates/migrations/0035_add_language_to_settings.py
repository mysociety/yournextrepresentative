# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0034_add_can_edit_settings_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='LANGUAGE',
            field=models.CharField(default='en', max_length=200, verbose_name='Language Code'),
        ),
    ]
