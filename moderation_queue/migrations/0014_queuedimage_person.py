# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0002_update_models_from_upstream'),
        ('moderation_queue', '0013_auto_20150916_1753'),
    ]

    operations = [
        migrations.AddField(
            model_name='queuedimage',
            name='person',
            field=models.ForeignKey(blank=True, null=True, to='popolo.Person'),
            preserve_default=False,
        ),
    ]
