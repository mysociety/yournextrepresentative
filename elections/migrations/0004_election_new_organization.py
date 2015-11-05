# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0002_update_models_from_upstream'),
        ('elections', '0003_allow_null_winner_membership_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='election',
            name='new_organization',
            field=models.ForeignKey(blank=True, to='popolo.Organization', null=True),
        ),
    ]
