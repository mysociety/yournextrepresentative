# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0036_postextra_election_unique_togther'),
        ('moderation_queue', '0017_suggestedpostlock'),
    ]

    operations = [
        migrations.AddField(
            model_name='suggestedpostlock',
            name='postextraelection',
            field=models.ForeignKey(blank=True, to='candidates.PostExtraElection', null=True),
        ),
    ]
