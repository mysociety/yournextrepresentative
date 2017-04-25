# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from django.db import migrations


def move_candidates_locked_to_postextraelection(apps, schema_editor):
    PostExtra = apps.get_model('candidates', 'PostExtra')
    PostExtraElection = apps.get_model('candidates', 'PostExtraElection')

    locks = PostExtra.objects.filter(candidates_locked=True)
    for lock in locks:
        for election in lock.elections.all():
            new_lock = PostExtraElection.objects.get(
                postextra=lock,
                election=election
            )
            new_lock.candidates_locked = True
            new_lock.save()


def move_candidates_locked_to_postextra(apps, schema_editor):
    """
    Because this locks at a post level it means the reverse migration
    is potentially lossy. In cases where a post has been in more than one
    election and not all of them are locked that data will be lost.
    However, it seemed better to be permissive in locking as I think it's
    easier to spot "Hey, why can't I edit this" that "Hey, I should not be
    able to edit this". Hopefully. Regardless, if you want to do this
    you need to set an env variable `ALLOW_LOSSY_REVERSE_MIGRATIONS=1`
    """
    if os.environ.get('ALLOW_LOSSY_REVERSE_MIGRATIONS') != '1':
        raise Exception(
            'Cannot reverse 0034_candidates_locked_data migration as it will \
            lose data. See the migration file for more details.'
        )
    PostExtraElection = apps.get_model('candidates', 'PostExtraElection')

    locks = PostExtraElection.objects.filter(candidates_locked=True)
    for lock in locks:
        pe = lock.postextra
        pe.candidates_locked = True
        pe.save()


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0033_postextraelection_candidates_locked'),
    ]

    operations = [
        migrations.RunPython(
            move_candidates_locked_to_postextraelection,
            move_candidates_locked_to_postextra
        )
    ]
