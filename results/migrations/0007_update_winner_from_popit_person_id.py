# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def popit_to_db(apps, schema_editor):
    Person = apps.get_model('popolo', 'person')
    ResultEvent = apps.get_model('results', 'resultevent')
    for res in ResultEvent.objects.all():
        if res.winner_popit_person_id:
            res.person = Person.objects.get(pk=res.winner_popit_person_id)
        else:
            res.person = None
        res.save()

def db_to_popit(apps, schema_editor):
    ResultEvent = apps.get_model('results', 'resultevent')
    for res in ResultEvent.objects.all():
        if res.person:
            res.winner_popit_person_id = res.person.id
        else:
            res.winner_popit_person_id = ''
        res.save()

class Migration(migrations.Migration):

    dependencies = [
        ('results', '0006_resultevent_winner'),
    ]

    operations = [
        migrations.RunPython(
            popit_to_db,
            db_to_popit,
        ),
    ]
