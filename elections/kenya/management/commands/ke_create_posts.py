# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from candidates.models import (
    AreaExtra, OrganizationExtra, PostExtra, PartySet, PostExtraElection, check_constraints
)
from elections.models import AreaType, Election
from popolo.models import Area, Organization, Post

import csv
import string


PARTY_SET_SLUG = 'kenya_2017'
PARTY_SET_NAME = 'Register of Politial Parties'

ELECTION_DATE = date(2017, 8, 8)

CONSISTENT_ELECTION_DATA = {
    'candidate_membership_role': 'Candidate',
    'election_date': date(2017, 8, 8),
    'current': True,
    'use_for_candidate_suggestions': False,
    'area_generation': 3,
}


class Command(BaseCommand):

    def get_or_create_area(self, identifier, name, classification, area_type):
        area, created = Area.objects.update_or_create(
            identifier=identifier,
            defaults={
                'name': name,
                'classification': classification,
            }
        )
        AreaExtra.objects.update_or_create(
            base=area,
            defaults={'type': area_type}
        )

        return area

    def get_or_create_organization(self, slug, name):
        try:
            org_extra = OrganizationExtra.objects.get(slug=slug)
            org = org_extra.base
            org.name = name
            org.save()
        except OrganizationExtra.DoesNotExist:
            org = Organization.objects.create(name=name)
            org_extra = OrganizationExtra.objects.create(base=org, slug=slug)
        return org

    def get_or_create_post(self, slug, label, organization, area, role, election, party_set):
        try:
            post_extra = PostExtra.objects.get(slug=slug)
            post = post_extra.base
        except PostExtra.DoesNotExist:
            post = Post.objects.create(
                label=label,
                organization=organization,
            )
            post_extra = PostExtra.objects.create(
                base=post,
                slug=slug,
            )
        post.area = area
        post.role = role
        post.label = label
        post.organization = organization
        post.save()
        post_extra.party_set = party_set
        post_extra.save()
        post_extra.elections.clear()
        PostExtraElection.objects.create(
            postextra=post_extra,
            election=election,
        )

        return post

    def areas_from_csv(self, csv_filename, code_column, name_column, county_id_restriction):
        # At this point we have the election, organisation and area types ready.
        # Iterate over the senators CSV to build our lists of other things to add.

        areas = {}

        reader = csv.DictReader(open('elections/kenya/data/' + csv_filename))
        for row in reader:

            if (county_id_restriction is not None) and county_id_restriction != row.get('County Code'):
                continue

            # In this script we only care about the areas, because we're building the posts
            # Actual candidates (and their parties) are done elsewhere

            area_id = row[code_column]

            # Do we already have this area?
            if area_id not in areas:

                # This is a dict rather than just a name in case we need to easily add anything in future.
                areas[area_id] = {
                    'id': area_id,
                    'name': string.capwords(row[name_column])
                }

        return areas

    def get_county_assembly_elections(self):
        county_areas = self.areas_from_csv(
            '2017_candidates_county_assemblies.csv',
            'County Code',
            'County Name',
            None)
        return [
            {
                'CANDIDATES_FILE': '2017_candidates_county_assemblies.csv',
                'ELECTION_NAME': '2017 {0} County Assembly Election'.format(county_area['name']),
                'ELECTION_SLUG': 'co-{0}-2017'.format(county_area['id']),
                'POST_ROLE': 'County Assembly Member',
                'POST_SLUG_PREFIX': 'co',
                'POST_LABEL_PREFIX': 'County Assembly Member for ',
                'AREA_TYPE_FOR_POSTS': 'WRD',
                'ORG_NAME': '{0} County Assembly'.format(county_area['name']),
                'ORG_SLUG': 'county:{0}-county-assembly'.format(county_area['id']),
                'COUNTY_ID_RESTRICTION': county_area['id'],
            }
            for county_area in county_areas.values()
        ]

    def get_all_elections(self):
        elections = [
            {
                'CANDIDATES_FILE': '2017_candidates_presidency.csv',
                'ELECTION_NAME': '2017 Presidential Election',
                'ELECTION_SLUG': 'pr-2017',
                'POST_SLUG': 'president',
                'POST_ROLE': 'President',
                'POST_SLUG_PREFIX': 'pr',
                'POST_LABEL_PREFIX': 'President of ',
                'AREA_TYPE_FOR_POSTS': 'CTR',
                'ORG_NAME': 'The Presidency',
                'ORG_SLUG': 'the-presidency'
            },
            {
                'CANDIDATES_FILE': '2017_candidates_senate.csv',
                'ELECTION_NAME': '2017 Senate Election',
                'ELECTION_SLUG': 'se-2017',
                'POST_ROLE': 'Senator',
                'POST_SLUG_PREFIX': 'se',
                'POST_LABEL_PREFIX': 'Senator for ',
                'AREA_TYPE_FOR_POSTS': 'DIS',
                'ORG_NAME': 'Senate of Kenya',
                'ORG_SLUG': 'senate-of-kenya'
            },
            {
                'CANDIDATES_FILE': '2017_candidates_wr.csv',
                'ELECTION_NAME': '2017 Women Representatives Election',
                'ELECTION_SLUG': 'wo-2017',
                'POST_ROLE': 'Women Representative',
                'POST_SLUG_PREFIX': 'wo',
                'POST_LABEL_PREFIX': 'Women Representative for ',
                'AREA_TYPE_FOR_POSTS': 'DIS',
                'ORG_NAME': 'National Assembly',
                'ORG_SLUG': 'national-assembly'
            },
            {
                'CANDIDATES_FILE': '2017_candidates_governors.csv',
                'ELECTION_NAME': '2017 County Governor Elections',
                'ELECTION_SLUG': 'go-2017',
                'POST_ROLE': 'County Governor',
                'POST_SLUG_PREFIX': 'go',
                'POST_LABEL_PREFIX': 'County Governor for ',
                'AREA_TYPE_FOR_POSTS': 'DIS',
                'ORG_NAME': 'County Governors',
                'ORG_SLUG': 'county-governors'
            },
            {
                'CANDIDATES_FILE': '2017_candidates_assembly.csv',
                'ELECTION_NAME': '2017 National Assembly Election',
                'ELECTION_SLUG': 'na-2017',
                'POST_ROLE': 'Member of the National Assembly',
                'POST_SLUG_PREFIX': 'na',
                'POST_LABEL_PREFIX': 'Member of the National Assembly for ',
                'AREA_TYPE_FOR_POSTS': 'CON',
                'ORG_NAME': 'National Assembly',
                'ORG_SLUG': 'national-assembly'
            }
        ]
        return elections + self.get_county_assembly_elections()

    @transaction.atomic
    def handle(self, *args, **options):

        # Make sure the PartySet exists
        party_set, created = PartySet.objects.update_or_create(
            slug=PARTY_SET_SLUG,
            defaults={
                'name': PARTY_SET_NAME
            }
        )

        for election_metadata in self.get_all_elections():

            # Set up the election
            election_data = {
                'slug': election_metadata['ELECTION_SLUG'],
                'for_post_role': election_metadata['POST_ROLE'],
                'name': election_metadata['ELECTION_NAME'],
                'organization_name': election_metadata['ORG_NAME'],
                'organization_slug': election_metadata['ORG_SLUG'],
                'party_lists_in_use': False,
            }

            org = self.get_or_create_organization(
                election_data['organization_slug'],
                election_data['organization_name'],
            )

            del election_data['organization_name']
            del election_data['organization_slug']
            election_data['organization'] = org

            election_slug = election_data.pop('slug')
            election_data.update(CONSISTENT_ELECTION_DATA)
            election, created = Election.objects.update_or_create(
                slug=election_slug,
                defaults=election_data,
            )

            # Create the AreaType for the country
            # DIS is the Kenya MapIt type for County/District
            area_type, created = AreaType.objects.get_or_create(
                name=election_metadata['AREA_TYPE_FOR_POSTS'],
                defaults={'source': 'MapIt'},
            )

            # Tie the AreaType to the election
            election.area_types.add(area_type)

            code_column, name_column, area_id_prefix, classification = {
                'CTR': (None, None, 'country:', 'Country'),
                'DIS': ('County Code', 'County Name', 'county:', 'County'),
                'CON': ('Constituency Code', 'Constituency Name', 'constituency:', 'Constituency'),
                'WRD': ('Ward Code', 'Ward Name', 'ward:', 'Ward')
            }[election_metadata['AREA_TYPE_FOR_POSTS']]

            if election_metadata['POST_ROLE'] == 'President':
                areas_for_posts = {
                    '1': {
                        'id': '1',
                        'name': 'Kenya',
                    }
                }
            else:
                areas_for_posts = self.areas_from_csv(
                    election_metadata['CANDIDATES_FILE'],
                    code_column,
                    name_column,
                    election_metadata.get('COUNTY_ID_RESTRICTION')
                )

            # By now areas_for_posts should contain one of each area.

            # Common stuff
            organization = election.organization
            post_role = election.for_post_role

            # For each area, make sure the area exists and make sure a post exists.
            for id, area in areas_for_posts.iteritems():

                area_object = self.get_or_create_area(
                    identifier=area_id_prefix + area['id'],
                    name=area['name'],
                    classification=classification,
                    area_type=area_type
                )

                post_label = election_metadata['POST_LABEL_PREFIX'] + area['name']
                post_slug = election_metadata['POST_SLUG_PREFIX'] + '-' + area['id']

                self.get_or_create_post(
                    slug=post_slug,
                    label=post_label,
                    organization=organization,
                    area=area_object,
                    role=post_role,
                    election=election,
                    party_set=party_set
                )

            errors = check_constraints()
            if errors:
                print errors
                raise Exception('Constraint errors detected. Aborting.')
