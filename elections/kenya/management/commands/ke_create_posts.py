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

PRESIDENCY_ORG_NAME = 'The Presidency'
PRESIDENCY_ORG_SLUG = 'the-presidency'

SENATE_ORG_NAME = 'Senate of Kenya'
SENATE_ORG_SLUG = 'senate-of-kenya'

ASSEMBLY_ORG_NAME = 'National Assembly'
ASSEMBLY_ORG_SLUG = 'national-assembly'

GOV_ORG_NAME = 'County Governors'
GOV_ORG_SLUG = 'county-governors'

WARD_ORG_NAME_SUFFIX = 'County Assembly'
WARD_ORG_SLUG_SUFFIX = 'county-assembly'


ELECTIONS = [
    {
        'CANDIDATES_FILE': '2017_candidates_presidency.csv',
        'ELECTION_NAME': '2017 Presidential Election',
        'ELECTION_SLUG': 'pres-2017',
        'POST_SLUG': 'president',
        'POST_ROLE': 'President',
        'AREA_TYPE': 'KECTR',
    },
    {
        'CANDIDATES_FILE': '2017_candidates_senate.csv',
        'ELECTION_NAME': '2017 Senate Election',
        'ELECTION_SLUG': 'senate-2017',
        'POST_ROLE': 'Senator',
        'POST_SLUG_PREFIX': 'senator',
        'POST_LABEL_PREFIX': 'Senator for ',
        'AREA_TYPE': 'KEDIS',
    },
    {
        'CANDIDATES_FILE': '2017_candidates_wr.csv',
        'ELECTION_NAME': '2017 Women Representatives Election',
        'ELECTION_SLUG': 'wr-2017',
        'POST_ROLE': 'Women Representative',
        'POST_SLUG_PREFIX': 'wr',
        'POST_LABEL_PREFIX': 'Women Representative for ',
        'AREA_TYPE': 'KEDIS',
    },
    {
        'CANDIDATES_FILE': '2017_candidates_governors.csv',
        'ELECTION_NAME': '2017 County Governor Elections',
        'ELECTION_SLUG': 'governor-2017',
        'POST_ROLE': 'County Governor',
        'POST_SLUG_PREFIX': 'governor',
        'POST_LABEL_PREFIX': 'County Governor for ',
        'AREA_TYPE': 'KEDIS',
    },
    {
        'CANDIDATES_FILE': '2017_candidates_assembly.csv',
        'ELECTION_NAME': '2017 National Assembly Election',
        'ELECTION_SLUG': 'assembly-2017',
        'POST_ROLE': 'Assembly Member',
        'POST_SLUG_PREFIX': 'assembly',
        'POST_LABEL_PREFIX': 'Assembly Member for ',
        'AREA_TYPE': 'KECON',
    }
]

WARD_CANDIDATES_FILE = '2017_candidates_county_assemblies.csv'
WARD_ELECTION_NAME_PREFIX = '2017'
WARD_ELECTION_NAME_SUFFIX = 'County Assembly Election'
WARD_ELECTION_SLUG_PREFIX = 'county-assembly-2017'
WARD_POST_ROLE = 'County Assembly Member'
WARD_POST_SLUG_PREFIX = 'county-assembly'
WARD_POST_LABEL_PREFIX = 'County Assembly Member for '


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


    def areas_from_csv(self, csv_filename, code_column, name_column):
        # At this point we have the election, organisation and area types ready.
        # Iterate over the senators CSV to build our lists of other things to add.

        areas = {}

        reader = csv.DictReader(open('elections/kenya/data/' + csv_filename))
        for row in reader:

            # In this script we only care about the areas, because we're building the posts
            # Actual candidates (and their parties) are done elsewhere

            area_id = row[code_column]

            # Do we already have this area?
            if area_id not in areas:

                # This is a dict rather than just a name in case we need to easily add anything in future.
                areas[area_id] = {
                    'id': area_id,
                    'name': row[name_column].title()
                }

        return areas

    def handle(self, *args, **options):

        # Make sure the PartySet exists
        party_set, created = PartySet.objects.update_or_create(
            slug=PARTY_SET_SLUG,
            defaults={
                'name': PARTY_SET_NAME
            }
        )

        consistent_election_data = {
            'candidate_membership_role': 'Candidate',
            'election_date': date(2017, 8, 8),
            'current': True,
            'use_for_candidate_suggestions': False,
            'area_generation': 3,
        }

        for election_metadata in ELECTIONS:

            with transaction.atomic():

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
                election_data.update(consistent_election_data)
                election, created = Election.objects.update_or_create(
                    slug=election_slug,
                    defaults=election_data,
                )

                # Create the AreaType for the country
                # DIS is the Kenya MapIt type for County/District
                area_type, created = AreaType.objects.get_or_create(
                    name=election_metadata['AREA_TYPE'],
                    defaults={'source': 'MapIt'},
                )

                # Tie the AreaType to the election
                election.area_types.add(area_type)

                code_column, name_column, area_id_prefix, classification = {
                    'KEDIS': ('County Code', 'County Name', 'county:', 'County'),
                    'KECON': ('Constituency Code', 'Constituency Name', 'constituency:', 'Constituency'),
                }[election_metadata['AREA_TYPE']]

                if election_metadata['POST_SLUG'] == 'president':
                    areas = {
                        'country:1': {
                            'id': 'country:1',
                            'name': 'Kenya',
                        }
                    }
                else:
                    areas = self.areas_from_csv(
                        election_metadata['CANDIDATES_FILE'], 'County Code', 'County Name')

                # By now areas should contain one of each area.

                # Common stuff
                organization = election.organization
                post_role = election.for_post_role

                # For each area, make sure the area exists and make sure a post exists.
                for id, area in areas.iteritems():

                    area = self.get_or_create_area(
                        identifier=area_id_prefix + area['id'],
                        name=area['name'],
                        classification=classification,
                        area_type=area_type
                    )

                    post_label = election_metadata['POST_LABEL_PREFIX'] + ' ' + area['name']
                    post_slug = election_metadata['POST_SLUG_PREFIX'] + '-' + area['id']

                    post = self.get_or_create_post(
                        slug=post_slug,
                        label=post_label,
                        organization=organization,
                        area=area,
                        role=post_role,
                        election=election,
                        party_set=party_set
                    )

                errors = check_constraints()
                if errors:
                    print errors
                    raise Exception('Constraint errors detected. Aborting.')

        return

        # COUNTY ASSEMBLY MEMBERS
        with transaction.atomic():

            # Iterate over the members CSV to build our lists of other things to add.

            counties = {}
            wards = {}

            reader = csv.DictReader(open('elections/kenya/data/' + WARD_CANDIDATES_FILE))
            for row in reader:

                # In this script we only care about the constituencies, because we're building the posts
                # Actual candidates (and their parties) are done elsewhere

                county_id = row['County Code']
                ward_id = row['Ward Code']

                # Do we already have this county?
                if county_id not in counties:

                    # This is a dict rather than just a name in case we need to easily add anything in future.
                    counties[county_id] = {
                        'id': county_id,
                        'name': row['County Name'].title()
                    }

                # Do we already have this ward?
                if ward_id not in wards:

                    # This is a dict rather than just a name in case we need to easily add anything in future.
                    wards[ward_id] = {
                        'id': ward_id,
                        'name': row['Ward Name'].title(),
                        'county_id': row['County Code']
                    }

            # These elections happen once for each county

            for id, county in counties.iteritems():

                # Set up the election
                election_data = {
                    'slug': 'county-' + id + '-' + WARD_ELECTION_SLUG_PREFIX,
                    'for_post_role': WARD_POST_ROLE,
                    'name': WARD_ELECTION_NAME_PREFIX + ' ' + county['name'] + ' ' + WARD_ELECTION_NAME_SUFFIX,
                    'organization_name': county['name'] + ' ' + WARD_ORG_NAME_SUFFIX,
                    'organization_slug': 'county:' + id + '-' + WARD_ORG_SLUG_SUFFIX,
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
                election_data.update(consistent_election_data)
                election, created = Election.objects.update_or_create(
                    slug=election_slug,
                    defaults=election_data,
                )

            # The area and post generation happens per ward

            for id, ward in wards.iteritems():

                # Create the AreaType for the country
                # WRD is the Kenya MapIt type for Ward
                area_type, created = AreaType.objects.get_or_create(
                    name='KEWRD',
                    defaults={'source': 'MapIt'},
                )

                # Get the relevant election
                election_slug = 'county-' + ward['county_id'] + '-' + WARD_ELECTION_SLUG_PREFIX
                election = Election.objects.get(slug=election_slug)

                # Tie the AreaType to the election
                election.area_types.add(area_type)

                # At this point we have the election, organisation and area types ready

                # By now constituencies should contain one of each county.

                # Common stuff
                organization = election.organization
                post_role = election.for_post_role

                area = self.get_or_create_area(
                    identifier='ward:' + ward['id'],
                    name=ward['name'],
                    classification='Ward',
                    area_type=area_type
                )

                post_label = WARD_POST_LABEL_PREFIX + ' ' + ward['name']
                post_slug = WARD_POST_SLUG_PREFIX + '-' + ward['id']

                post = self.get_or_create_post(
                    slug=post_slug,
                    label=post_label,
                    organization=organization,
                    area=area,
                    role=post_role,
                    election=election,
                    party_set=party_set
                )

            errors = check_constraints()
            if errors:
                print errors
                raise Exception('Constraint errors detected. Aborting.')
