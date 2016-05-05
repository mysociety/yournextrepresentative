# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0023_auto_20160505_1636'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resultset',
            name='num_spoilt_ballots',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='resultset',
            name='num_turnout_reported',
            field=models.IntegerField(null=True),
        ),
    ]
