import requests
from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand
from django.conf import settings

from uk_results.models import Council
from uk_results import constants


class Command(BaseCommand):
    def handle(self, **options):
        EE_BASE_URL = getattr(
            settings, "EE_BASE_URL", "https://elections.democracyclub.org.uk/")

        # Import organisations from EE
        url = "{}api/organisations/".format(EE_BASE_URL)
        while url:
            req = requests.get(url)
            data = req.json()
            for org_dict in data['results']:
                self.process_org(org_dict)
            url = data.get('next')

    def process_org(self, org_dict):
        if org_dict['organisation_type'] != "local-authority":
            return

        council, created = Council.objects.update_or_create(
            pk=org_dict['official_identifier'],
            council_type=org_dict['organisation_subtype'],
            defaults={
                'slug': org_dict['slug'],
                'name': org_dict['official_name']
            }
        )
