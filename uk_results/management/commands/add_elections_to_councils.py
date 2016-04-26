import os
import csv
from datetime import date

from django.core.management.base import BaseCommand
from slugify import slugify

from candidates.models import PartySet
from uk_results.models import Council, CouncilElection
from elections.models import Election


class Command(BaseCommand):
    GB_PARTY_SET = PartySet.objects.get(slug='gb')

    date = date(2016, 5, 5)

    def election_id_from_line(self, line):
        election_type = 'local'
        election_subtype = self.authority_name_to_slug(line['council_name'])
        return ".".join([
            election_type,
            election_subtype,
            self.date.strftime("%Y-%m-%d")
        ])

    def authority_name_to_slug(self, authority_name):
        authority_name = authority_name.lower().strip()
        authority_name = slugify(authority_name)
        return authority_name


    def handle(self, **options):
        csv_path = os.path.abspath(
            "elections/uk/data/2016-local-elections-wards.csv")
        csv_file = csv.DictReader(open(csv_path))

        for line in csv_file:
            print(line['council_gss'], line['council_name'])
            council = Council.objects.get(pk=line['council_gss'])
            election_id = self.election_id_from_line(line)
            election = Election.objects.get(slug=election_id)


            CouncilElection.objects.update_or_create(
                election=election,
                council=council,
                defaults={
                    'party_set': self.GB_PARTY_SET,
                }
            )
