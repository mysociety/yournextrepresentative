# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0036_migrate_language_to_db'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='TIME_ZONE',
            field=models.CharField(default='Europe/London', max_length=200, verbose_name='Time Zone'),
        ),
    ]
