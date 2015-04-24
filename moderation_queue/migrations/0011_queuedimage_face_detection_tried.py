# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('moderation_queue', '0010_auto_add_crop_bounds'),
    ]

    operations = [
        migrations.AddField(
            model_name='queuedimage',
            name='face_detection_tried',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
