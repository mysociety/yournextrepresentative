# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def popit_to_db(apps, schema_editor):
    Person = apps.get_model('popolo', 'person')
    QueuedImage = apps.get_model('moderation_queue', 'queuedimage')
    for qi in QueuedImage.objects.all():
        try:
            qi.person = Person.objects.get(pk=qi.popit_person_id)
            qi.save()
        except Person.DoesNotExist:
            # QueueImage objects may refer to someone who has since
            # been deleted from PopIt.
            pass


def db_to_popit(apps, schema_editor):
    QueuedImage = apps.get_model('moderation_queue', 'queuedimage')
    for qi in QueuedImage.objects.all():
        if qi.person:
            qi.popit_person_id = qi.person.id
            qi.save()


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0002_update_models_from_upstream'),
        ('moderation_queue', '0014_queuedimage_person'),
    ]

    operations = [
        migrations.RunPython(
            popit_to_db,
            db_to_popit,
        ),
    ]
