# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0018_electionarea_noc'),
    ]

    operations = [
        migrations.AddField(
            model_name='councilelection',
            name='confirming_result_set',
            field=models.OneToOneField(null=True, to='uk_results.CouncilElectionResultSet'),
        ),
    ]
