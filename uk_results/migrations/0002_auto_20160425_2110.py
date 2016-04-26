# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0002_update_models_from_upstream'),
        ('elections', '0012_election_people_elected_per_post'),
        ('uk_results', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Council',
            fields=[
                ('council_id', models.CharField(max_length=100, serialize=False, primary_key=True)),
                ('council_type', models.CharField(max_length=10, blank=True)),
                ('mapit_id', models.CharField(max_length=100, blank=True)),
                ('name', models.CharField(max_length=255, blank=True)),
                ('email', models.EmailField(max_length=254, blank=True)),
                ('phone', models.CharField(max_length=100, blank=True)),
                ('website', models.URLField(blank=True)),
                ('postcode', models.CharField(max_length=100, null=True, blank=True)),
                ('address', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='CouncilElection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('council', models.ForeignKey(to='uk_results.Council')),
                ('election', models.ForeignKey(to='elections.Election')),
            ],
        ),
        migrations.CreateModel(
            name='CouncilElectionResultSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('source', models.TextField(null=True)),
                ('controller', models.ForeignKey(to='popolo.Organization', null=True)),
                ('council_election', models.ForeignKey(to='uk_results.CouncilElection')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterModelOptions(
            name='resultset',
            options={},
        ),
        migrations.RemoveField(
            model_name='resultset',
            name='confirmed_by',
        ),
        migrations.RemoveField(
            model_name='resultset',
            name='is_final',
        ),
        migrations.AddField(
            model_name='candidateresult',
            name='source',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='resultset',
            name='source',
            field=models.TextField(null=True),
        ),
    ]
