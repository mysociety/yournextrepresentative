# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('moderation_queue', '0002_auto_20150213_0838'),
    ]

    operations = [
        migrations.AlterField(
            model_name='queuedimage',
            name='justification_for_use',
            field=models.TextField(blank=True),
            preserve_default=True,
        ),
    ]
