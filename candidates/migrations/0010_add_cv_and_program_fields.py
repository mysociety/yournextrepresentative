# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0009_migrate_to_django_popolo'),
    ]

    operations = [
        migrations.AddField(
            model_name='personextra',
            name='cv',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='personextra',
            name='program',
            field=models.TextField(blank=True),
        ),
    ]
