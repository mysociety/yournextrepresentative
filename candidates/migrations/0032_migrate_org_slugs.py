# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations

def add_missing_classifications(apps):
    Organization = apps.get_model('popolo', 'Organization')

    for org in Organization.objects.filter(classification=""):
        if org.name.endswith(' Police') or org.name.endswith(' Constabulary'):
            org.classification = "police_area"
            org.save()

    mapping = {
        "London Assembly": "gla",
        "Greater London Authority": "gla",
        "National Assembly for Wales": "naw",
        "Northern Ireland Assembly": "nia",
        "Scottish Parliament": "sp",
    }
    for name, classification in mapping.items():
        Organization.objects.filter(name=name).update(
            classification=classification)

    for org in Organization.objects.filter(classification=""):
        org.classification = "local-authority"
        org.save()


def add_classification_to_slugs(apps, schema_editor):
    if settings.ELECTION_APP != 'uk':
        return
    add_missing_classifications(apps)
    OrganizationExtra = apps.get_model('candidates', 'OrganizationExtra')

    for ox in OrganizationExtra.objects.exclude(base__classification="Party"):
        if not ox.slug.startswith(ox.base.classification):
            ox.slug = ":".join([
                ox.base.classification,
                ox.slug
            ])
            ox.save()

def remove_classification_from_slugs(apps, schema_editor):
    if settings.ELECTION_APP != 'uk':
        return
    OrganizationExtra = apps.get_model('candidates', 'OrganizationExtra')

    for ox in OrganizationExtra.objects.all():
        if ox.slug.startswith(ox.base.classification) and ":" in ox.slug:
            ox.slug = ox.slug.split(":")[1]
            if not OrganizationExtra.objects.filter(slug=ox.slug).exists():
                ox.save()

class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0031_loggedaction_post'),
    ]

    operations = [
        migrations.RunPython(
            add_classification_to_slugs,
            remove_classification_from_slugs
        )
    ]
