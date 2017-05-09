# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0030_populate_postresult_post_election'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='postresult',
            name='post',
        ),
        migrations.AlterField(
            model_name='postresult',
            name='post_election',
            field=models.ForeignKey(
                to='candidates.PostExtraElection', null=False),
        ),

    ]
