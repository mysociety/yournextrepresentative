# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('moderation_queue', '0005_migrate_data_to_why_allowed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='queuedimage',
            name='public_domain',
        ),
        migrations.RemoveField(
            model_name='queuedimage',
            name='use_allowed_by_owner',
        ),
    ]
