# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0011_auto_20160427_1305'),
    ]

    operations = [
        migrations.RenameField(
            model_name='resultset',
            old_name='post',
            new_name='post_result',
        ),
    ]
