import os
import csv
from datetime import date

import requests

from django.core.management.base import BaseCommand
from slugify import slugify

from uk_results.models import CouncilElection, ElectionArea

class Command(BaseCommand):
    MAPIT_URL = "http://mapit.democracyclub.org.uk/"
    HEADERS = {'User-Agent': 'scraper/sym',}
    SIMPLIFY_TOLERANCE = 0.0009

    def get_geo_json_from_mapit(self, gss):
        req = requests.get("{}area/{}".format(
            self.MAPIT_URL,
            gss
        ), headers=self.HEADERS)
        req = requests.get("{}.geojson?simplify_tolerance={}".format(
            req.url,
            self.SIMPLIFY_TOLERANCE
        ), headers=self.HEADERS)
        return req.content

    def handle(self, **options):
        self.import_council_areas()
        self.import_concil_wards()

    def import_council_areas(self):
        for council_election in CouncilElection.objects.all():
            geojson = self.get_geo_json_from_mapit(council_election.council.pk)
            ElectionArea.objects.update_or_create(
                area_gss=council_election.council.pk,
                election=council_election.election,
                parent=None,
                area_name=council_election.council.name,
                defaults={
                    'geo_json': geojson
                }
            )

    def import_concil_wards(self):
        for council_election in CouncilElection.objects.all():
            for post in council_election.election.posts.all():
                parent_gss = council_election.council.pk
                gss = post.base.area.identifier.split(':')[1]
                area_name = post.base.area.name
                geojson = self.get_geo_json_from_mapit(gss)
                parent = ElectionArea.objects.get(area_gss=parent_gss)
                ElectionArea.objects.update_or_create(
                    area_gss=gss,
                    election=council_election.election,
                    parent=parent,
                    area_name=area_name,
                    defaults={
                        'geo_json': geojson
                    }
                )
