# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def migrate_to_popolo_organizations(apps, schema_editor):
    Election = apps.get_model('elections', 'Election')
    Organization = apps.get_model('popolo', 'Organization')
    OrganizationExtra = apps.get_model('candidates', 'OrganizationExtra')
    for e in Election.objects.all():
        # This is a get_or_create, rather than just get, because when
        # running tests with an ELECTION_APP that has a case in
        # 0002_auto_20151012_1731 it will have Election objects with
        # an organization_id set, but no corresponding Organization
        # object.  So that the migration doesn't fail when creating
        # the database for tests, create the organization if it
        # doesn't exist.
        try:
            o_extra = OrganizationExtra.objects.get(
                slug=e.organization_id
            )
            o = o_extra.base
        except OrganizationExtra.DoesNotExist:
            o = Organization.objects.create(
                name=e.organization_name
            )
            o_extra = OrganizationExtra.objects.create(
                base=o,
                slug=e.organization_id,
            )
        e.new_organization = o
        e.save()

class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0004_election_new_organization'),
        ('candidates', '0009_migrate_to_django_popolo'),
    ]

    operations = [
        migrations.RunPython(
            migrate_to_popolo_organizations,
            lambda apps, schema_editor: None
        )
    ]
