# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('moderation_queue', '0015_migrate_queuedimage_person'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='queuedimage',
            name='popit_person_id',
        ),
    ]
