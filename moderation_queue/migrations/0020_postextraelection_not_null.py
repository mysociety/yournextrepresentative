# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('moderation_queue', '0019_migrate_post_extra_to_postextraelection'),
    ]

    operations = [
        migrations.AlterField(
            model_name='suggestedpostlock',
            name='postextraelection',
            field=models.ForeignKey(to='candidates.PostExtraElection'),
        ),
    ]
