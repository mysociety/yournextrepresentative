# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0007_councilelectionresultset_noc'),
    ]

    operations = [
        migrations.AddField(
            model_name='councilelection',
            name='confirmed',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='councilelectionresultset',
            name='council_election',
            field=models.ForeignKey(related_name='reported_results', to='uk_results.CouncilElection'),
        ),
    ]
