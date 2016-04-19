# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_auto_20160418_1226'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='persontask',
            options={'ordering': ['-task_priority']},
        ),
    ]
