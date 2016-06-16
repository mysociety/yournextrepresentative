import csv
import requests

from django.core.management.base import BaseCommand
from django.db import transaction

from popolo.models import Person, Membership
from elections.models import Election


"""
Grab a list of MPs post 2010 election from TWFY and use that
to update YNR using parlparse IDs
"""
class Command(BaseCommand):
    help = "Import the list of UK 2010 general election winners"

    def handle(self, **options):
        # CSV of MPs post 2010 election
        url = "http://www.theyworkforyou.com/mps/?f=csv&date=2010-06-01"
        r = requests.get(
            url,
            stream=True,
        )
        r.raise_for_status()
        winners = csv.DictReader(r.raw)
        election = Election.objects.get(slug='2010')
        count = 0
        with transaction.atomic():
            for winner in winners:
                parlparse_id = 'uk.org.publicwhip/person/{0}'.format(
                    winner['Person ID']
                )
                person = Person.objects.get(
                    identifiers__scheme='uk.org.publicwhip',
                    identifiers__identifier=parlparse_id
                )

                try:
                    membership = person.memberships.get(
                        extra__election=election,
                        role='Candidate',
                        post__organization__extra__slug='commons',
                    )
                except Membership.DoesNotExist:
                    print("failed to find a membership for {0}").format(
                        parlparse_id
                    )
                    continue

                count += 1
                membership.extra.elected = True
                membership.extra.save()

        print("matched {0} memberships".format(count))
