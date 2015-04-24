# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('moderation_queue', '0009_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='queuedimage',
            name='crop_max_x',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='queuedimage',
            name='crop_max_y',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='queuedimage',
            name='crop_min_x',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='queuedimage',
            name='crop_min_y',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
