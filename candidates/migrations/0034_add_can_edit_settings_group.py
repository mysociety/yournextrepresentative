# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from auth_helpers.migrations import (
    get_migration_group_create,
    get_migration_group_delete,
)
from candidates.models import EDIT_SETTINGS_GROUP_NAME


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0033_migrate_settings_to_db'),
    ]

    operations = [
        migrations.RunPython(
            get_migration_group_create(EDIT_SETTINGS_GROUP_NAME, []),
            get_migration_group_delete(EDIT_SETTINGS_GROUP_NAME),
        )
    ]
