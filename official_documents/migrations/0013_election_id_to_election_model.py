# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def election_to_election_model(apps, schema_editor):
    Election = apps.get_model('elections', 'election')
    Document = apps.get_model('official_documents', 'officialdocument')
    for doc in Document.objects.all():
        doc.election_model = Election.objects.get(slug=doc.election)
        doc.save()


def election_model_to_election(apps, schema_editor):
    Document = apps.get_model('official_documents', 'officialdocument')
    for doc in Document.objects.all():
        doc.election = doc.election_model.id
        doc.save()


class Migration(migrations.Migration):

    dependencies = [
        ('official_documents', '0012_officialdocument_election_model'),
    ]

    operations = [
        migrations.RunPython(
            election_to_election_model,
            election_model_to_election,
        ),
    ]
