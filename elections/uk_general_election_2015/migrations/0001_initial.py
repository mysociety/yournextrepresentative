# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import json
import os

from django.db import migrations

from elections.uk_general_election_2015 import mapit

logger = logging.getLogger(__name__)


def mapit_ids_to_gss(apps, schema_editor):
    Area = apps.get_model("popolo", "Area")

    mapit_data = json.loads(open(
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
                     "0001_mapit_data_cache.json"), 'r').read())

    for area in Area.objects.all():
        old_id = area.identifier
        try:
            mapit_area = mapit_data[area.identifier]
            new_id = mapit.format_code_from_area(mapit_area)

            if old_id != new_id:
                area.identifier = new_id
                area.save()
                print("Changed ID {0} to {1}".format(old_id, new_id))

        except KeyError:
            print("No GSS code found for {}".format(area.identifier))


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0002_update_models_from_upstream'),
        ('candidates', '0009_migrate_to_django_popolo'),
    ]

    operations = [
        migrations.RunPython(mapit_ids_to_gss),
    ]
