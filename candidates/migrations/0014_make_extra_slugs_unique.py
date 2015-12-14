# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0013_remove_max_popit_ids'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizationextra',
            name='slug',
            field=models.CharField(unique=True, max_length=256, blank=True),
        ),
        migrations.AlterField(
            model_name='partyset',
            name='slug',
            field=models.CharField(unique=True, max_length=256),
        ),
        migrations.AlterField(
            model_name='postextra',
            name='slug',
            field=models.CharField(unique=True, max_length=256, blank=True),
        ),
    ]
