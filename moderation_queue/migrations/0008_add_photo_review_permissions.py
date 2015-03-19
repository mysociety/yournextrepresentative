# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from auth_helpers.migrations import (
    get_migration_group_create,
    get_migration_group_delete,
)
from moderation_queue.models import PHOTO_REVIEWERS_GROUP_NAME


class Migration(migrations.Migration):

    dependencies = [
        ('moderation_queue', '0007_auto_20150303_1420'),
    ]

    operations = [
        migrations.RunPython(
            get_migration_group_create(
                PHOTO_REVIEWERS_GROUP_NAME, ['change_queuedimage']
            ),
            get_migration_group_delete(
                PHOTO_REVIEWERS_GROUP_NAME
            )
        )
    ]
