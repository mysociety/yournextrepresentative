# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0010_make_post_id_format_optional'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='election',
            name='post_id_format',
        ),
    ]
