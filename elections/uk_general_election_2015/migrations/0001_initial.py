# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import logging
import json
import os

from django.db import migrations

from elections.uk_general_election_2015 import mapit

logger = logging.getLogger(__name__)


def get_mapit_data():
    old_mapit_data_filename = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "0001_mapit_data_cache.json"
    )
    with open(old_mapit_data_filename) as f:
        return json.load(f)

def mapit_ids_to_gss(apps, schema_editor):
    Area = apps.get_model("popolo", "Area")

    mapit_data = get_mapit_data()

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


def gss_to_old_mapit_ids(apps, schema_editor):
    Area = apps.get_model("popolo", "Area")

    code_to_old_mapit_area_id = {}
    old_mapit_data = get_mapit_data()

    for old_mapit_id, area_data in old_mapit_data.items():
        for code_type, code_id in area_data.get('codes', {}).items():
            key = '{0}:{1}'.format(code_type, code_id)
            code_to_old_mapit_area_id[key] = old_mapit_id

    for area in Area.objects.all():
        gss_id = area.identifier
        try:
            old_mapit_area_id = code_to_old_mapit_area_id[gss_id]
            area.identifier = old_mapit_area_id
            area.save()
        except KeyError:
            print("No old MapIt Area ID found for {}".format(area.identifier))


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0002_update_models_from_upstream'),
        ('candidates', '0009_migrate_to_django_popolo'),
    ]

    operations = [
        migrations.RunPython(
            mapit_ids_to_gss,
            gss_to_old_mapit_ids,
        )
    ]
