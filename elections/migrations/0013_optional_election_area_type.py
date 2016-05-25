# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0012_election_people_elected_per_post'),
    ]

    operations = [
        migrations.AlterField(
            model_name='election',
            name='area_types',
            field=models.ManyToManyField(to='elections.AreaType', blank=True),
        ),
    ]
