# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0032_rename_postresult_to_postelectionresult'),
    ]

    operations = [
        migrations.RenameField(
            model_name='resultset',
            old_name='post_result',
            new_name='post_election_result',
        ),
    ]
