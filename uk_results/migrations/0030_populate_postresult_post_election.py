# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import defaultdict

from django.db import migrations, models


def set_post_election_from_post(apps, schema_editor):
    """
    This is far from ideal. Try to guess the PostExtraElection
    that this PostResult relates to. This will have to be done by looking
    and the related memberships and assuming they're correct (sometimes they
    won't be, and that will have to be fixed manually later).
    """
    PostResult = apps.get_model('uk_results', 'PostResult')
    PostExtraElection = apps.get_model('candidates', 'PostExtraElection')

    qs = PostResult.objects.all().select_related('post__extra')
    for post_result in qs:
        pee = None
        elections = post_result.post.extra.elections.all()
        if not elections.exists():
            raise ValueError("Post with no elections found.")
        if elections.count() == 1:
            # This is an easy case – this post only has one known election
            pee = PostExtraElection.objects.get(
                election=elections.first(),
                postextra=post_result.post.extra
            )
            post_result.post_election = pee
            post_result.save()

        else:
            if not post_result.result_sets.exists():
                # There are no results sets for this post_result
                # so we can just delete it
                post_result.delete()
                continue

            result_sets_by_election = defaultdict(list)
            # Work out how many elections we have results for.
            # If it's only 1, then use that one
            for result_set in post_result.result_sets.all():
                for candidate_result in result_set.candidate_results.all():
                    this_election = candidate_result.membership.extra.election
                    result_sets_by_election[this_election].append(result_set)

            if len(set(result_sets_by_election.keys())) == 1:
                election = result_sets_by_election.keys()[0]
                pee = PostExtraElection.objects.get(
                    election=election,
                    postextra=post_result.post.extra
                )
                post_result.post_election = pee
                post_result.save()

            else:
                # We have results for more than one election, but only
                # a single PostResult object.
                # Split the result_sets up in to a new PostResult per election
                for election, result_sets in result_sets_by_election.items():
                    result_sets = set(result_sets)
                    pee = PostExtraElection.objects.get(
                        election=election,
                        postextra=post_result.post.extra
                    )
                    pr = PostResult.objects.create(
                        post_election=pee,
                        post=post_result.post,
                        confirmed=post_result.confirmed,
                        confirmed_resultset=post_result.confirmed_resultset
                    )
                    for result_set in result_sets:
                        result_set.post_result = pr
                        result_set.save()
                post_result.delete()




class Migration(migrations.Migration):

    dependencies = [
        ('uk_results', '0029_add_postresult_post_election'),
    ]

    operations = [
        migrations.RunPython(set_post_election_from_post),
    ]
