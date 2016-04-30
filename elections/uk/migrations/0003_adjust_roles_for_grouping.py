# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.db import migrations


def adjust_roles_for_grouping(apps, schema_editor):
    Election = apps.get_model('elections', 'Election')
    for election in Election.objects.all():
        if re.search(r'^local\.[^.]+\.2016', election.slug):
            election.for_post_role = 'Local Councillor'
            election.save()
        if re.search(r'^mayor\.[^.]+\.2016', election.slug):
            election.for_post_role = 'Mayor'
            election.save()


class Migration(migrations.Migration):

    dependencies = [
        ('uk', '0002_remove-gb-prefix'),
    ]

    operations = [
        migrations.RunPython(adjust_roles_for_grouping),
    ]
