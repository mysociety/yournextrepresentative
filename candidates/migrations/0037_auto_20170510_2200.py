# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0036_postextra_election_unique_togther'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loggedaction',
            name='created',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
    ]
