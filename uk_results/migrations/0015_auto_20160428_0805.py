# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0012_election_people_elected_per_post'),
        ('uk_results', '0014_auto_20160427_1429'),
    ]

    operations = [
        migrations.CreateModel(
            name='ElectionArea',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('area_gss', models.CharField(max_length=100)),
                ('area_name', models.CharField(max_length=255, blank=True)),
                ('geo_json', models.TextField(blank=True)),
                ('election', models.ForeignKey(to='elections.Election')),
                ('parent', models.ForeignKey(to='uk_results.ElectionArea', null=True)),
            ],
        ),
        migrations.AlterModelOptions(
            name='candidateresult',
            options={'ordering': ('num_ballots_reported',)},
        ),
    ]
