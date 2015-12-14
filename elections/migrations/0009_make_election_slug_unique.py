# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0008_remove_artificial_start_and_end_dates'),
    ]

    operations = [
        migrations.AlterField(
            model_name='election',
            name='slug',
            field=models.CharField(unique=True, max_length=128),
        ),
    ]
