from datetime import datetime
from os.path import join
import re
import json
from slugify import slugify

from django.core.management.base import BaseCommand
from django.conf import settings

from slumber.exceptions import HttpServerError
import dateutil.parser

from candidates.popit import create_popit_api_object

# For a version with only current parties, you can use this URL as an
# argument to the command:
#
#   https://raw.githubusercontent.com/DemocracyClub/UK-Political-Parties/gh-pages/data/parties.csv
#
# ... or for one which also includes de-registered parties, you can
# use this URL:
#
#   https://raw.githubusercontent.com/mhl/UK-Political-Parties/gh-pages/data/parties.csv

party_name_re = re.compile(
    r'^(.*?)(?:\s+\[De-registered\s+(\d{2}/\d{2}/\d{2})\])?\s*$'
)

class Command(BaseCommand):
    help = "Update parties from a CSV of party data"

    def handle(self, **options):
        self.api = create_popit_api_object()
        scraper_directory = join(
            settings.BASE_DIR, 'data', 'UK-Political-Parties', 'scraper'
        )
        self.parse_data(
            join(scraper_directory, 'all_data.json'),
            join(scraper_directory, 'raw_data'),
        )

    def parse_data(self, json_file, raw_data_directory):
        with open(json_file) as f:
            for ec_party in json.load(f):
                ec_party_id = ec_party['party_id'].strip()
                # We're only interested in political parties:
                if not ec_party_id.startswith('PP'):
                    continue
                party_id = self.clean_id(ec_party_id)
                register = ec_party.get('register')
                if not register:
                    continue
                register = re.sub(r' \(minor party\)', '', register)
                party_name, party_dissolved = self.clean_name(
                    ec_party['party_name'], register
                )
                party_founded = self.clean_date(ec_party['registered_date'])
                party_data = {
                    'id': party_id,
                    'name': party_name,
                    'slug': slugify(party_name),
                    'classification': 'Party',
                    'founding_date': party_founded,
                    'dissolution_date': party_dissolved,
                    'register': register,
                    'identifiers': [
                        {
                            'identifier': party_id,
                            'scheme': 'electoral-commission',
                        }
                    ]
                }
                try:
                    self.api.organizations.post(party_data)
                except HttpServerError as e:
                    error = json.loads(e.content)
                    if error.get('error', {}).get('code') == 11000:
                        # Duplicate Party Found
                        self.api.organizations(party_id).put(party_data)

    def clean_date(self, date):
        return dateutil.parser.parse(date).strftime("%Y-%m-%d")

    def clean_name(self, name, register):
        m = party_name_re.search(name)
        name, party_dissolved = m.groups()
        if party_dissolved:
            party_dissolved = datetime.strptime(party_dissolved, '%d/%m/%y')
            party_dissolved = str(party_dissolved.date())
        else:
            # Currently missing out the dissolution date completely to
            # indicate 'future' makes using PopIt's search endpoint
            # difficult, so use a far-future value if the party is
            # still active.
            party_dissolved = '9999-12-31'
        return name.strip(), party_dissolved

    def clean_id(self, party_id):
        party_id = re.sub(r'^PPm?\s*', '', party_id).strip()
        return "party:{0}".format(party_id)
