# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0002_auto_20151012_1731'),
    ]

    operations = [
        migrations.AlterField(
            model_name='election',
            name='winner_membership_role',
            field=models.CharField(max_length=128, null=True, blank=True),
        ),
    ]
