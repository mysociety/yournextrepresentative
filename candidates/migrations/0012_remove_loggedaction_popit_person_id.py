# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0011_migrate_loggedaction_person'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='loggedaction',
            name='popit_person_id',
        ),
    ]
