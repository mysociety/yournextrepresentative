# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0002_update_models_from_upstream'),
        ('candidates', '0009_migrate_to_django_popolo'),
    ]

    operations = [
        migrations.AddField(
            model_name='loggedaction',
            name='person',
            field=models.ForeignKey(blank=True, to='popolo.Person', null=True),
        ),
    ]
