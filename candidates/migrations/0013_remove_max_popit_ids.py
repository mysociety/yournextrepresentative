# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0012_remove_loggedaction_popit_person_id'),
    ]

    operations = [
        migrations.DeleteModel(
            name='MaxPopItIds',
        ),
    ]
