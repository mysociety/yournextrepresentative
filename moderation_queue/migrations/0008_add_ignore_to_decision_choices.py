# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('moderation_queue', '0007_auto_20150303_1420'),
    ]

    operations = [
        migrations.AlterField(
            model_name='queuedimage',
            name='decision',
            field=models.CharField(default='undecided', max_length=32, choices=[('approved', 'Approved'), ('rejected', 'Rejected'), ('undecided', 'Undecided'), ('ignore', 'Ignore')]),
            preserve_default=True,
        ),
    ]
