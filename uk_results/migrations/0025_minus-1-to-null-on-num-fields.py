# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def move_minus_one_to_null(apps, schema_editor):
    ResultSet = apps.get_model("uk_results", "resultset")
    ResultSet.objects.filter(num_turnout_reported=-1).update(
        num_turnout_reported=None)
    ResultSet.objects.filter(num_spoilt_ballots=-1).update(
        num_spoilt_ballots=None)




class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0024_auto_20160505_2334'),
    ]

    operations = [
        migrations.RunPython(move_minus_one_to_null),
    ]
