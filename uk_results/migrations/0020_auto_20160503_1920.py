# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0019_councilelection_confirming_result_set'),
    ]

    operations = [
        migrations.RenameField(
            model_name='councilelection',
            old_name='confirming_result_set',
            new_name='controller',
        ),
    ]
