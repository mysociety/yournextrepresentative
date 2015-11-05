# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0006_remove_old_organization_fields'),
    ]

    operations = [
        migrations.RenameField(
            model_name='election',
            old_name='new_organization',
            new_name='organization',
        ),
    ]
