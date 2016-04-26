# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0002_auto_20160425_2110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='councilelection',
            name='council',
            field=models.OneToOneField(to='uk_results.Council'),
        ),
        migrations.AlterField(
            model_name='councilelection',
            name='election',
            field=models.OneToOneField(to='elections.Election'),
        ),
    ]
