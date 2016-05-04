# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0020_auto_20160503_1920'),
    ]

    operations = [
        migrations.RenameField(
            model_name='councilelection',
            old_name='controller',
            new_name='controller_resultset',
        ),
    ]
