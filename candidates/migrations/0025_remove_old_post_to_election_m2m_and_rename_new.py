# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0024_port_existing_post_to_election_m2m_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='postextra',
            name='elections',
        ),
        migrations.RenameField('PostExtra', 'new_elections', 'elections'),
        migrations.AlterField(
            model_name='postextra',
            name='elections',
            field=models.ManyToManyField(related_name='posts', through='candidates.PostExtraElection', to='elections.Election'),
        ),
    ]
