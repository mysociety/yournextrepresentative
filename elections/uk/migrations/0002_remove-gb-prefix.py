# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

IDS_TO_ALTER = {
    "gb-nia-2016-05-05": "nia-2016-05-05",
    "gb-sp-2016-05-05-c": "sp-2016-05-05-c",
    "gb-naw-2016-05-05-c": "naw-2016-05-05-c",
    "gb-sp-2016-05-05-r": "sp-2016-05-05-r",
    "gb-naw-2016-05-05-r": "naw-2016-05-05-r",
    "gb-gla-2016-05-05-a": "gla-2016-05-05-a",
    "gb-gla-2016-05-05-c": "gla-2016-05-05-c",

}


def remove_gb_prefix(apps, schema_editor):
    Election = apps.get_model("elections", "Election")

    for election in Election.objects.filter(slug__in=IDS_TO_ALTER.keys()):
        election.slug = IDS_TO_ALTER[election.slug]
        election.save()


def add_gb_prefix(apps, schema_editor):
    Election = apps.get_model("elections", "Election")
    reversed_ids_to_alter = dict((v, k) for k, v in IDS_TO_ALTER.iteritems())

    for election in Election.objects.filter(
            slug__in=reversed_ids_to_alter.keys()):
        election.slug = reversed_ids_to_alter[election.slug]
        election.save()


class Migration(migrations.Migration):

    dependencies = [
        ('uk', '0001_migrate_area_ids'),
    ]

    operations = [
        migrations.RunPython(
            remove_gb_prefix,
            add_gb_prefix,
        )
    ]
