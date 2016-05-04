# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0021_auto_20160503_1923'),
    ]

    operations = [
        migrations.AddField(
            model_name='postresult',
            name='confirmed_resultset',
            field=models.OneToOneField(null=True, to='uk_results.ResultSet'),
        ),
    ]
