from django.core.management.base import BaseCommand

from candidates.models import PartySet
from uk_results.models import Council, CouncilElection
from elections.models import Election
from uk_results.constants import RESULTS_DATE


class Command(BaseCommand):

    def handle(self, **options):
        gb_party_set = PartySet.objects.get(slug='gb')

        qs = Election.objects.filter(
            organization__extra__slug__startswith="local-authority:",
            election_date=RESULTS_DATE)

        for election in qs:
            org = election.organization
            council_type, council_id = org.extra.slug.split(":")
            council = Council.objects.get(slug=council_id)

            CouncilElection.objects.update_or_create(
                election=election,
                council=council,
                defaults={
                    'party_set': gb_party_set,
                }
            )
