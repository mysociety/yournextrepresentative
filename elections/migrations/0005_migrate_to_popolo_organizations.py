# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def migrate_to_popolo_organizations(apps, schema_editor):
    Election = apps.get_model('elections', 'Election')
    Organization = apps.get_model('popolo', 'Organization')
    for e in Election.objects.all():
        o = Organization.objects.get(extra__slug=e.organization_id)
        e.new_organization = o
        e.save()

class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0004_election_new_organization'),
        ('candidates', '0008_membershipextra_organizationextra_personextra_postextra'),
    ]

    operations = [
        migrations.RunPython(
            migrate_to_popolo_organizations,
            lambda apps, schema_editor: None
        )
    ]
