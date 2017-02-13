from __future__ import print_function, unicode_literals

from django.core.management.base import BaseCommand, CommandError

from candidates.models import MembershipExtra, PostExtraElection


class Command(BaseCommand):

    help = 'A one-off command to fix a past data inconsistency issue'

    def handle(self, *args, **options):
        for me in MembershipExtra.objects.select_related(
                'base__post__extra', 'election', 'base__person'):
            election = me.election
            if not election:
                continue
            postextra = me.base.post.extra
            if not postextra:
                msg = "The Post for Membership with ID {0} had no " \
                      "MembershipExtra"
                raise CommandError(msg.format(me.base.id))
            if not PostExtraElection.objects.filter(
                    postextra=me.base.post.extra,
                    election=me.election).exists():
                msg = "Making a PostExtraElection for election {0} and post {1}"
                print(msg.format(election.slug, postextra.slug))
                PostExtraElection.objects.create(
                    postextra=postextra,
                    election=election)
