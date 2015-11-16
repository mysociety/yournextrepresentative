# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('official_documents', '0016_auto_20151116_1259'),
    ]

    operations = [
        migrations.AlterField(
            model_name='officialdocument',
            name='election',
            field=models.ForeignKey(to='elections.Election'),
        ),
    ]
