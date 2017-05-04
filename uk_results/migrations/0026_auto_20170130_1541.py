# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0025_minus-1-to-null-on-num-fields'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='councilelectionresultset',
            options={'get_latest_by': 'modified'},
        ),
        migrations.AlterModelOptions(
            name='resultset',
            options={'get_latest_by': 'modified'},
        ),
    ]
