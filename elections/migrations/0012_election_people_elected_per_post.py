# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0011_remove_election_post_id_format'),
    ]

    operations = [
        migrations.AddField(
            model_name='election',
            name='people_elected_per_post',
            field=models.IntegerField(default=1, help_text='The number of people who are elected to this post in the election.  -1 means a variable number of winners'),
        ),
    ]
