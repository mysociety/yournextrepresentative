# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0027_auto_20170502_2130'),
    ]

    operations = [
        migrations.RenameField(
            model_name='council',
            old_name='mapit_id',
            new_name='slug',
        ),
    ]
