from __future__ import print_function, unicode_literals

import os
import csv
from datetime import date
from collections import defaultdict

from django.core.management.base import BaseCommand

from slugify import slugify

from candidates.models import (
    AreaExtra, OrganizationExtra, PartySet, PostExtra, PostExtraElection
)
from elections.models import AreaType, Election
from popolo.models import Area, Organization, Post

COUNCIL_TO_WARD_TYPE_CODES = {
    'DIS': 'DIW',
    'MTD': 'MTW',
    'UTA': 'UTW',
    'CTY': 'CED'
}


class Command(BaseCommand):
    help = 'Create posts and elections for the 2016 PCC elections'

    def handle(self, **options):
        self.date = date(2016, 5, 5)
        self.gb_parties, _ = PartySet.objects.get_or_create(
            slug='gb', defaults={'name': 'Great Britain'}
        )

        self.elections = self.create_elections_dict_from_csv()

        for election_id, election in self.elections.items():
            election['organisation_object'] = \
                self.create_organisation(election_id, election)
            election['election_object'] =\
                self.create_election(election_id, election)
            for post in election['posts']:
                self.add_area(post, election)

    def authority_name_to_slug(self, authority_name):
        authority_name = authority_name.lower().strip()
        authority_name = slugify(authority_name)
        return authority_name

    def election_id_from_line(self, line):
        election_type = 'local'
        election_subtype = self.authority_name_to_slug(line['council_name'])
        return ".".join([
            election_type,
            election_subtype,
            self.date.strftime("%Y-%m-%d")
        ])

    def create_elections_dict_from_csv(self):

        elections = defaultdict(dict)
        csv_path = os.path.abspath(
            "elections/uk/data/2016-local-elections-wards.csv")
        csv_file = csv.DictReader(open(csv_path))
        for line in csv_file:
            election_id = self.election_id_from_line(line)
            area_type = COUNCIL_TO_WARD_TYPE_CODES[line['council_code_type']]

            if line['have_ward_boundaries'] == "n" or not line['ward_gss']:
                elections[election_id]['have_ward_boundaries'] = False
                ward_id = "NODATA:{0}-{1}".format(
                    line['council_gss'],
                    slugify(line['ward_name'])
                )
                ward_slug = ward_id
            else:
                elections[election_id]['have_ward_boundaries'] = True
                ward_id = "gss:"+line['ward_gss']
                ward_slug = "{0}:{1}".format(
                    area_type,
                    line['ward_gss']
                )

            elections[election_id]['authority_name'] = line['council_name']
            elections[election_id]['authority_id'] = line['council_gss']
            elections[election_id]['authority_slug'] = \
                slugify(line['council_name'])
            posts = elections[election_id].get('posts', [])


            posts.append({
                'ward_id': ward_id,
                'ward_name': line['ward_name'],
                'ward_slug': ward_slug,
                'ward_seats': line['ward_seats'],
                'area_type': area_type,
                'parent_id': "gss:" + line['council_gss'],
                'parent_name': line['council_name'],
                'parent_code_type': line['council_code_type'],
            })
            elections[election_id]['posts'] = posts
        return elections

    def create_organisation(self, election_id, election):
        org_name = election['authority_name']
        org_slug = election['authority_slug']

        try:
            organization_extra = OrganizationExtra.objects.get(slug=org_slug)
            organization = organization_extra.base
        except OrganizationExtra.DoesNotExist:
            organization = Organization.objects.create(name=org_name)
            organization_extra = OrganizationExtra.objects.create(
                base=organization,
                slug=org_slug
                )
        return organization_extra

    def create_election(self, election_id, election):
        election_defaults = {
            'party_lists_in_use': False,
            'name': "{0} local election".format(election['authority_name']),
            'for_post_role': "Councillor for {0}".format(
                election['authority_name']),
            'area_generation': 1,
            'election_date': self.date
        }
        election_defaults['current'] = True
        election_defaults['candidate_membership_role'] = 'Candidate'
        election_slug = election_id
        print('Creating:', election_defaults['name'], '...',)
        election, created = Election.objects.update_or_create(
            slug=election_slug,
            defaults=election_defaults
        )
        if created:
            print('[created]')
        else:
            print('[already existed]')
        return election

    def add_area(self, post_dict, election):

        area_type, _ = AreaType.objects.update_or_create(
            name=post_dict['area_type'],
            defaults={'source': 'MapIt'}
        )

        if not election['election_object'].area_types.filter(
                name=area_type.name).exists():
            election['election_object'].area_types.add(area_type)

        parent_area = None
        if not election['have_ward_boundaries']:
            parent_area_type, _ = AreaType.objects.update_or_create(
                name=post_dict['parent_code_type'],
                defaults={'source': 'MapIt'}
            )

            parent_area, _ = Area.objects.get_or_create(
                identifier=post_dict['parent_id'],
                defaults={'name': post_dict['parent_name']}
                name=post_dict['parent_name']
            )

            AreaExtra.objects.get_or_create(
                base=parent_area,
                type=parent_area_type
            )

        area, _ = Area.objects.update_or_create(
            identifier=post_dict['ward_id'],
            defaults={
                'name': "{0} ward".format(post_dict['ward_name']),
                'parent': parent_area,
            }
        )
        AreaExtra.objects.get_or_create(base=area, type=area_type)

        post, _ = Post.objects.update_or_create(
            organization=election['organisation_object'].base,
            area=area,
            defaults={
                'role': post_dict['ward_slug'],
                'label': "{0} ward".format(post_dict['ward_name']),
            })
        post_extra, _ = PostExtra.objects.update_or_create(
            base=post,
            defaults={
                'slug': post_dict['ward_slug'],
                'party_set': self.gb_parties,
            },
        )

        PostExtraElection.objects.update_or_create(
            postextra=post_extra,
            election=election['election_object'],
            winner_count=post_dict['ward_seats']
        )
