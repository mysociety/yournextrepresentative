# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0017_auto_20160429_0938'),
    ]

    operations = [
        migrations.AddField(
            model_name='electionarea',
            name='noc',
            field=models.BooleanField(default=False),
        ),
    ]
