# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cached_counts', '0004_constituency_to_post'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CachedCount',
        ),
    ]
