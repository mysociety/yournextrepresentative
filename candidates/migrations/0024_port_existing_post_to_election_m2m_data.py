# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def old_post_election_m2m_to_new(apps, schema_editor):
    PostExtraElection = apps.get_model('candidates', 'PostExtraElection')
    PostExtra = apps.get_model('candidates', 'PostExtra')
    for post in PostExtra.objects.all():
        for election in post.elections.all():
            PostExtraElection.objects.get_or_create(
                postextra=post,
                election=election
            )


def new_post_election_m2m_to_old(apps, schema_editor):
    PostExtra = apps.get_model('candidates', 'PostExtra')

    for post in PostExtra.objects.all():
        for election in post.new_elections.all():
            post.elections.add(election)


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0023_create_post_to_elections_m2m_with_extra_fields'),
    ]

    operations = [
        migrations.RunPython(
            old_post_election_m2m_to_new,
            new_post_election_m2m_to_old
        )
    ]
