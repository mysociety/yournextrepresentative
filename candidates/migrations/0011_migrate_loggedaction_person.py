# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

def popit_to_db(apps, schema_editor):
    Person = apps.get_model('popolo', 'person')
    LoggedAction = apps.get_model('candidates', 'loggedaction')
    for la in LoggedAction.objects.all():
        if la.popit_person_id:
            try:
                la.person = Person.objects.get(pk=la.popit_person_id)
            except Person.DoesNotExist:
                # LoggedAction objects may refer to someone who has
                # since been deleted from PopIt.
                la.person = None
        else:
            la.person = None
        la.save()

def db_to_popit(apps, schema_editor):
    LoggedAction = apps.get_model('candidates', 'loggedaction')
    for la in LoggedAction.objects.all():
        if la.person:
            la.popit_person_id = la.person.id
        else:
            la.popit_person_id = ''
        la.save()


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0010_loggedaction_person'),
    ]

    operations = [
        migrations.RunPython(
            popit_to_db,
            db_to_popit,
        ),
    ]
