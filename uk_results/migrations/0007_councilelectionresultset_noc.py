# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0006_add_admin_persmissions'),
    ]

    operations = [
        migrations.AddField(
            model_name='councilelectionresultset',
            name='noc',
            field=models.BooleanField(default=False),
        ),
    ]
