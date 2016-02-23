
from __future__ import print_function, unicode_literals

from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.six.moves.urllib_parse import urljoin
from django.utils.text import slugify

import requests

from candidates.models import AreaExtra, OrganizationExtra, PartySet, PostExtra
from elections.models import AreaType, Election
from elections.uk import mapit
from popolo.models import Area, Organization, Post


class Command(BaseCommand):
    help = 'Create posts and elections for the 2016 PCC elections'

    def handle(self, **options):

        mapit_url = settings.MAPIT_BASE_URL

        self.gb_parties, _ = PartySet.objects.get_or_create(
            slug='gb', defaults={'name': 'Great Britain'}
        )

        self.organizations = {}

        self.base_election_info = {
            'name': 'Police and Crime Commissioner Elections 2016',
            'for_post_role': 'Police and Crime Commissioner',
            'label_format': 'Police and Crime Commissioner for {area_name}',
            'area_generation': 1,
            'election_date': date(2016, 5, 5),
            'party_lists_in_use': False,
            'mapit_code': 'PDG',
            'electon_id_prefix': 'pcc',
            # 'area_type_description': 'Police Force',
        }

        url_path = '/areas/' + self.base_election_info['mapit_code']
        url = urljoin(mapit_url, url_path)
        r = requests.get(url)
        mapit_results = r.json().items()

        # First make all the organisations
        for mapit_area_id, mapit_area_data in mapit_results:
            if mapit_area_data['codes']['police_id'] == "metropolitan":
                continue
            self.add_police_force_orgs(mapit_area_id, mapit_area_data)

        # Create a single election
        self.create_pcc_election()
        # Add all the areas for that election
        for mapit_area_id, mapit_area_data in mapit_results:
            if mapit_area_data['codes']['police_id'] == "metropolitan":
                # The Met doesn't have a PCCge
                continue
            self.add_pcc_areas(mapit_area_id, mapit_area_data)

    def add_police_force_orgs(self, mapit_area_id, mapit_area_data):
        org_name = mapit_area_data['name']
        org_slug = self.format_org_slug(org_name)

        try:
            organization_extra = OrganizationExtra.objects.get(slug=org_slug)
            organization = organization_extra.base
        except OrganizationExtra.DoesNotExist:
            organization = Organization.objects.create(name=org_name)
            organization_extra = OrganizationExtra.objects.create(
                base=organization,
                slug=org_slug
                )
        self.organizations[org_name] = organization

    def format_org_slug(self, org_name):
        name = org_name.lower()\
            .replace('police', '')\
            .replace('constabulary', '')\
            .strip()
        return slugify(name)

    def format_election_slug(self, election_info):
        return ".".join([
            election_info['electon_id_prefix'],
            election_info['election_date'].strftime('%Y-%m-%d')])

    def create_pcc_election(self):

        election_defaults = {
            k: self.base_election_info[k] for k in [
                'name', 'for_post_role', 'area_generation', 'election_date',
                'party_lists_in_use']
        }
        election_defaults['current'] = True
        election_defaults['candidate_membership_role'] = 'Candidate'
        # election_defaults['organization'] = self.organizations[org_name]
        election_defaults['name']
        election_slug = self.format_election_slug(
            self.base_election_info,
        )
        print('Creating:', election_defaults['name'], '...',)
        self.election, created = Election.objects.update_or_create(
            slug=election_slug,
            defaults=election_defaults
        )
        if created:
            print('[created]')
        else:
            print('[already existed]')

    def add_pcc_areas(self, mapit_area_id, mapit_area_data):
        org_name = mapit_area_data['name']

        area_type, _ = AreaType.objects.update_or_create(
            name=self.base_election_info['mapit_code'],
            defaults={'source': 'MapIt'}
        )

        if not self.election.area_types.filter(name=area_type.name).exists():
            self.election.area_types.add(area_type)

        area, _ = Area.objects.update_or_create(
            identifier=mapit.format_code_from_area(mapit_area_data),
            defaults={'name': mapit_area_data['name']}
        )

        # Now make sure that the MapIt codes are present as identifiers:
        for scheme, identifier in mapit_area_data['codes'].items():
            area.other_identifiers.update_or_create(
                scheme=scheme,
                defaults={'identifier': identifier},
            )

        AreaExtra.objects.get_or_create(base=area, type=area_type)
        post, _ = Post.objects.update_or_create(
            organization=self.organizations[org_name],
            area=area,
            role='Police and Crime Commissioner for {area_name}'.format(
                area_name=org_name
            ),
            defaults={
                'label': self.base_election_info['label_format'].format(
                    area_name=area.name
                )
            })
        post_extra, _ = PostExtra.objects.update_or_create(
            base=post,
            defaults={
                'slug': mapit.format_code_from_area(mapit_area_data),
                'party_set': self.gb_parties,
            },
        )
        post_extra.elections.add(self.election)
