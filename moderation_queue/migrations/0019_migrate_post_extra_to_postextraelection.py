# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import defaultdict
import os

from django.db import migrations, models

def migrate_post_extra_to_postextraelection(apps, schema_editor):
    SuggestedPostLock = apps.get_model('moderation_queue', 'SuggestedPostLock')
    for spl in SuggestedPostLock.objects.all():
        # If there's more than one postextraelection, then make sure
        # that we create new SuggestedPostLocks for the rest of them:
        postextraelections = spl.post_extra.postextraelection_set.all()
        use_for_original, use_for_new_list = \
            postextraelections[0], postextraelections[1:]
        # Update the SuggestedPostLock on the original:
        spl.use_for_original.postextraelection = use_for_original
        spl.save()
        # Then if there are any other PostExtraElection objects
        # associated with the post, create new SuggestPostLocks with
        # the same metadata for those as well.
        for postextraelection in use_for_new_list:
            SuggestedPostLock.objects.create(
                postextraelection=postextraelection,
                post_extra=spl.post_extra,
                user=spl.user,
                justification=spl.justification
            )
    
def migrate_postextraelection_to_post_extra(apps, schema_editor):
    # The reverse migration here will probably lose data, since we're
    # moving from the more expressive model (you can have a suggested
    # post lock for just one election that a post is associated with)
    # to the less expressive mmodel (a suggested post lock is for a
    # post, not specifying which election it applies to). So by
    # default, this migration will raise an exception to stop you
    # losing data on rolling back. If you wish to run this reverse
    # migration anyway, (e.g. in your local dev environment) please
    # set the environment variable ALLOW_LOSSY_REVERSE_MIGRATIONS to
    # '1', in which case the exception won't be raised, and a rollback
    # will be attempted anyway.
    if os.environ.get('ALLOW_LOSSY_REVERSE_MIGRATIONS') != '1':
        raise Exception(
            'Cannot reverse the 0019_migrate_post_extra_to_postextraelection ' \
            'migration as it will lose data. See the migration file for ' \
            'details on how to do this anyway.'
        )    
    SuggestedPostLock = apps.get_model('moderation_queue', 'SuggestedPostLock')
    # Group these by postextra, user and justification:
    grouped = defaultdict(list)
    for spl in list(SuggestedPostLock.objects.all()):
        key = (spl.postextraelection.postextra, spl.user, spl.justification)
        grouped[key].append(spl)
    # Now just keep one SuggestedPostLock in each of these groups:
    for t, spls_in_group in grouped.items():
        to_keep, to_delete_list = spls_in_group[0], spls_in_group[1:]
        to_keep.post_extra = to_keep.postextraelection.postextra
        to_keep.save()
        for to_delete in to_delete_list:
            to_delete.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('moderation_queue', '0018_suggestedpostlock_postextraelection'),
    ]

    operations = [
        migrations.RunPython(
            migrate_post_extra_to_postextraelection,
            migrate_postextraelection_to_post_extra,
        )
    ]
