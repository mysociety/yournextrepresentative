# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0009_make_election_slug_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='election',
            name='post_id_format',
            field=models.CharField(max_length=128, blank=True),
        ),
    ]
