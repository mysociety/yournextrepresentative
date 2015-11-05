# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

def popit_to_db(apps, schema_editor):
    Person = apps.get_model('popolo', 'person')
    LoggedAction = apps.get_model('candidates', 'loggedaction')
    for la in LoggedAction.objects.all():
        la.person = Person.objects.get(pk=la.popit_person_id)
        la.save()

def db_to_popit(apps, schema_editor):
    LoggedAction = apps.get_model('candidates', 'loggedaction')
    for la in LoggedAction.objects.all():
        la.popit_person_id = la.person.id
        la.save()


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0011_loggedaction_person'),
    ]

    operations = [
        migrations.RunPython(
            popit_to_db,
            db_to_popit,
        ),
    ]
