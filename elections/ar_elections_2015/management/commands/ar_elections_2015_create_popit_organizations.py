from django.core.management.base import BaseCommand

from candidates.election_specific import PARTY_DATA
from candidates.models.popit import create_or_update
from candidates.popit import PopItApiMixin

class Command(PopItApiMixin, BaseCommand):
    help = "Create the parties for the 2015 elections in Argentina"

    def handle(self, **options):

        for party_data in PARTY_DATA.all_party_data:
            create_or_update(
                self.api.organizations,
                party_data,
            )
