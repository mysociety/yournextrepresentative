# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0005_migrate_to_popolo_organizations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='election',
            name='organization_id',
        ),
        migrations.RemoveField(
            model_name='election',
            name='organization_name',
        ),
    ]
