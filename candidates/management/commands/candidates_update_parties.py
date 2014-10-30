from datetime import datetime
import os
import csv
import urllib2
import re
import json

from django.core.management.base import LabelCommand, CommandError
from django.conf import settings

from popit_api import PopIt
from slumber.exceptions import HttpServerError
import dateutil.parser

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

class Command(LabelCommand):
    help = "Update parties from a CSV of party data"

    def handle_label(self, label, **options):
        self.api = PopIt(
            instance=settings.POPIT_INSTANCE,
            hostname=settings.POPIT_HOSTNAME,
            port=getattr(settings, 'POPIT_PORT', 80),
            api_version='v0.1',
            api_key=settings.POPIT_API_KEY
           )


        if os.path.exists(label):
            with open(label) as csv_content:
                self.parse_csv(csv_content)
        else:
            csv_content = urllib2.urlopen(label)
            self.parse_csv(csv_content)

    def parse_csv(self, csv_content):

        reader = csv.DictReader(csv_content)
        for line in reader:
            if line['Entity type'] != 'Political Party':
                continue
            party_id = self.clean_id(line['EC Reference Number'])
            register = line['Register']
            party_name, party_dissolved = self.clean_name(line['Entity name'], register)
            party_founded = self.clean_date(line['Date of registration / notification'])
            party_data = {
                'id': party_id,
                'name': party_name,
                'classification': 'Party',
                'founding_date': party_founded,
                'dissolution_date': party_dissolved,
                'register': register,
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
        if register == "Northern Ireland":
            name = "{0} (Northern Ireland)".format(name)
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
        party_id = re.sub(r'^PPm? ', '', party_id).strip()
        return "party:{0}".format(party_id)
