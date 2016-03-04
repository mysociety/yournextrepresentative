# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0012_election_people_elected_per_post'),
        ('candidates', '0022_create_standard_simple_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostExtraElection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('winner_count', models.IntegerField(null=True, blank=True)),
                ('election', models.ForeignKey(to='elections.Election')),
                ('postextra', models.ForeignKey(to='candidates.PostExtra')),
            ],
        ),
        migrations.AddField(
            model_name='postextra',
            name='new_elections',
            field=models.ManyToManyField(related_name='new_posts', through='candidates.PostExtraElection', to='elections.Election'),
        ),
    ]
