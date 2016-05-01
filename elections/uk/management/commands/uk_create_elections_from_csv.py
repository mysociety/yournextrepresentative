from __future__ import print_function, unicode_literals

from compat import StreamDictReader
import re


import requests
from slugify import slugify

from django.core.management.base import BaseCommand


from candidates.models import (
    AreaExtra, OrganizationExtra, PartySet, PostExtra, PostExtraElection
)
from elections.models import AreaType, Election
from popolo.models import Area, Organization, Post

PARENT_TO_CHILD_AREAS = {
    'DIS': 'DIW',
    'MTD': 'MTW',
    'UTA': 'UTW',
    'CTY': 'CED',
    'LBO': 'LBW',
    'CED': 'CPC',
}
CHILD_TO_PARENT_AREAS = {
    'DIW': 'DIS',
    'MTW': 'MTD',
    'UTW': 'UTA',
    'UTE': 'UTA',
    'CED': 'CTY',
    'LBW': 'LBO',
    'CPC': 'CED',
}
HEADERS = {'User-Agent': 'scraper/sym', }


class Command(BaseCommand):
    help = 'Create posts and elections from a CSV file at a URL'

    args = "<CSV_URL>"


    def handle(self, *args, **options):
        csv_url, = args
        r = requests.get(csv_url)
        r.encoding = 'utf-8'
        reader = StreamDictReader(r.text)
        for line in reader:
            cleaned_line = {}
            for k,v in line.items():
                cleaned_line[k] = strip(v)
            if not cleaned_line['Election ID']:
                continue
            if not cleaned_line['GSS Code']:
                continue
            self.process_line(cleaned_line)

    def process_line(self, line):
        # Create the elections
        election = self.get_election(line)
        area_info = self.get_area_info(line)
        organization_extra = self.get_or_create_organisation(
            election, line, area_info)
        self.add_area(line, area_info, election, organization_extra)

    def clean_election_id(self, election_id):
        """
        extra checks to make sure IDs are correct
        """
        election_id = election_id.strip()
        election_id = election_id.replace("'", "")
        election_id = election_id.replace("&", "and")
        election_id = election_id.replace("-.", ".")

        return election_id

    def get_election(self, line):
        election_id = self.clean_election_id(line['Election ID'])
        election_date = line['Date']
        return Election.objects.update_or_create(
            slug=election_id,
            election_date=election_date,
            current=True,
            defaults={
                "name": line['Election Name'],
                "for_post_role": line['For Post Role'],
                "candidate_membership_role": "Candidate",
                "show_official_documents": True,
            }
        )[0]

    def get_area_info(self, line):
        area_info = {}
        area_code = line['GSS Code']
        if re.match('[ENSW]\d{8}$', area_code):
            area_code_type = "gss"
        else:
            area_code_type = "unit_id"

        req = requests.get("http://mapit.democracyclub.org.uk/code/{}/{}".format(
            area_code_type,
            area_code,
        ), headers=HEADERS)
        url = req.url
        area_data = req.json()
        area_type = area_data['type']
        area_type_name = area_data['type_name']
        area_generation = area_data['generation_low']

        area_info['area_code'] = area_code
        area_info['area_code_type'] = area_code_type
        area_info['area_type'] = area_type
        area_info['area_type_name'] = area_type_name
        area_info['area_generation'] = area_generation

        if area_type not in ['WMC', ]:
            parent_type = CHILD_TO_PARENT_AREAS[area_type]

            req = requests.get("{}/covered?type={}".format(
                url,
                parent_type,
            ), headers=HEADERS)

            parent_data = req.json().values()[0]
            parent_code = parent_data['codes'][area_code_type]
            area_info['parent_type'] = parent_type
            area_info['parent_code'] = parent_code
            area_info['parent_name'] = parent_data['name']
        return area_info

    def get_or_create_organisation(self, election, line, area_info):
        if line['Election Type'] == "parl":
            org_name = "House of Commons"
            org_slug = "commons"
            classification = "UK House of Parliament"
        else:
            org_name = line['Authority / Council']
            org_slug = slugify(org_name)
            classification = area_info['area_type_name']

        try:
            organization_extra = OrganizationExtra.objects.get(
                slug=org_slug)
            organization = organization_extra.base
        except OrganizationExtra.DoesNotExist:
            organization, _ = Organization.objects.get_or_create(
                name=org_name,
                defaults={'classification': classification})
            organization_extra = OrganizationExtra.objects.create(
                base=organization,
                slug=org_slug
                )
        return organization_extra


    def add_area(self, line, area_info, election, organization_extra):
        if line['Country'] == "ni":
            partyset_name = "Northern Ireland"
        else:
            partyset_name = "Great Britain"

        party_set, _ = PartySet.objects.get_or_create(
            slug=line["Country"], defaults={'name': partyset_name}
        )


        area_type, _ = AreaType.objects.update_or_create(
            name=area_info['area_type'],
            defaults={'source': 'MapIt'}
        )

        if not election.area_types.filter(
                name=area_type.name).exists():
            election.area_types.add(area_type)

        parent_area = None
        if 'parent_type' in area_info:
            parent_area_type, _ = AreaType.objects.update_or_create(
                name=area_info['parent_type'],
                defaults={'source': 'MapIt'}
            )

            parent_area, _ = Area.objects.get_or_create(
                identifier="{}:{}".format(
                        area_info['parent_type'],
                        area_info['parent_code']
                    ),
                defaults={'name': area_info['parent_name']}
            )

            AreaExtra.objects.get_or_create(
                base=parent_area,
                defaults={'type': parent_area_type}
            )

        if line['Election Type'] == "parl":
            area_name = line['Constituency / Ward']
            post_label = "Member of Parliament for {}".format(area_name)
            post_role = "Member of Parliament"
            post_extra_slug = line['mySociety mapit ID']
        else:
            area_name = "{} {}".format(
                    line['Constituency / Ward'],
                    line['Area Type'],
                )
            post_label = area_name
            post_role = "{}:{}".format(
                    area_info['area_type'],
                    area_info['area_code']
                )
            post_extra_slug = "{}:{}".format(
                    area_info['area_type'],
                    area_info['area_code']
                )

        area, _ = Area.objects.update_or_create(
            identifier="{}:{}".format(
                    area_info['area_type'],
                    area_info['area_code']
                ),
            defaults={
                'name': area_name,
                'parent': parent_area,
            }
        )

        AreaExtra.objects.get_or_create(
            base=area,
            defaults={'type': area_type}
        )

        post, _ = Post.objects.update_or_create(
            organization=organization_extra.base,
            area=area,
            defaults={
                'role': post_role,
                'label': area_name,
            })

        post_extra, _ = PostExtra.objects.update_or_create(
            base=post,
            defaults={
                'slug': post_extra_slug,
                'party_set': party_set,
            },
        )

        PostExtraElection.objects.update_or_create(
            postextra=post_extra,
            election=election,
            defaults={
                'winner_count': line['Number of seats']
            }
        )
