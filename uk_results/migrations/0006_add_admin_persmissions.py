# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from auth_helpers.migrations import (
    get_migration_group_create,
    get_migration_group_delete,
)

from uk_results.models import (
    TRUSTED_TO_CONFIRM_CONTROL_RESULTS_GROUP_NAME,
    TRUSTED_TO_CONFIRM_VOTE_RESULTS_GROUP_NAME,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0005_auto_20160426_1058'),
    ]

    operations = [
        migrations.RunPython(
            get_migration_group_create(
                TRUSTED_TO_CONFIRM_CONTROL_RESULTS_GROUP_NAME, []),
            get_migration_group_delete(
                TRUSTED_TO_CONFIRM_CONTROL_RESULTS_GROUP_NAME),
        ),
        migrations.RunPython(
            get_migration_group_create(
                TRUSTED_TO_CONFIRM_VOTE_RESULTS_GROUP_NAME, []),
            get_migration_group_delete(
                TRUSTED_TO_CONFIRM_VOTE_RESULTS_GROUP_NAME),
        )
    ]
