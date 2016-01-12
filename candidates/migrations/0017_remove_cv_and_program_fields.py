# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0016_migrate_data_to_extra_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='personextra',
            name='cv',
        ),
        migrations.RemoveField(
            model_name='personextra',
            name='program',
        ),
    ]
