# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0002_update_models_from_upstream'),
        ('uk_results', '0015_auto_20160428_0805'),
    ]

    operations = [
        migrations.CreateModel(
            name='PartyWithColour',
            fields=[
                ('hex_value', models.CharField(max_length=100, blank=True)),
                ('party', models.OneToOneField(primary_key=True, serialize=False, to='popolo.Organization')),
            ],
        ),
        migrations.AddField(
            model_name='electionarea',
            name='winning_party',
            field=models.ForeignKey(to='uk_results.PartyWithColour', null=True),
        ),
    ]
