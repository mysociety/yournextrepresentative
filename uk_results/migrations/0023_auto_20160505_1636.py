# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0022_postresult_confirmed_resultset'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='candidateresult',
            options={'ordering': ('-num_ballots_reported',)},
        ),
    ]
