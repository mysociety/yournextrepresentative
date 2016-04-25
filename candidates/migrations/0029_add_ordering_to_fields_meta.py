# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0028_create_order_attr_of_extra'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='complexpopolofield',
            options={'ordering': ('order',)},
        ),
        migrations.AlterModelOptions(
            name='extrafield',
            options={'ordering': ('order',)},
        ),
        migrations.AlterModelOptions(
            name='simplepopolofield',
            options={'ordering': ('order',)},
        ),
    ]
