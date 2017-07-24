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

PRESIDENCY_ELECTION_NAME = '2017 Presidential Election'
PRESIDENCY_ELECTION_SLUG = 'pres-2017'
PRESIDENCY_POST_SLUG = 'president'
PRESIDENCY_POST_ROLE = 'President'

SENATE_CANDIDATES_FILE = '2017_candidates_senate.csv'
SENATE_ELECTION_NAME = '2017 Senate Election'
SENATE_ELECTION_SLUG = 'senate-2017'
SENATE_POST_ROLE = 'Senator'
SENATE_POST_SLUG_PREFIX = 'senator'
SENATE_POST_LABEL_PREFIX = 'Senator for '

WR_CANDIDATES_FILE = '2017_candidates_wr.csv'
WR_ELECTION_NAME = '2017 Women Representatives Election'
WR_ELECTION_SLUG = 'wr-2017'
WR_POST_ROLE = 'Women Representative'
WR_POST_SLUG_PREFIX = 'wr'
WR_POST_LABEL_PREFIX = 'Women Representative for '

GOV_CANDIDATES_FILE = '2017_candidates_governors.csv'
GOV_ELECTION_NAME = '2017 County Governor Elections'
GOV_ELECTION_SLUG = 'governor-2017'
GOV_POST_ROLE = 'County Governor'
GOV_POST_SLUG_PREFIX = 'governor'
GOV_POST_LABEL_PREFIX = 'County Governor for '

ASSEMBLY_CANDIDATES_FILE = '2017_candidates_assembly.csv'
ASSEMBLY_ELECTION_NAME = '2017 National Assembly Election'
ASSEMBLY_ELECTION_SLUG = 'assembly-2017'
ASSEMBLY_POST_ROLE = 'Assembly Member'
ASSEMBLY_POST_SLUG_PREFIX = 'assembly'
ASSEMBLY_POST_LABEL_PREFIX = 'Assembly Member for '

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

    def handle(self, *args, **options):

        # Make sure the PartySet exists
        party_set, created = PartySet.objects.get_or_create(slug=PARTY_SET_SLUG)

        # PRESIDENCY
        with transaction.atomic():

            # Set up the election
            election_data = {
                'slug': PRESIDENCY_ELECTION_SLUG,
                'for_post_role': PRESIDENCY_POST_ROLE,
                'name': PRESIDENCY_ELECTION_NAME,
                'organization_name': PRESIDENCY_ORG_NAME,
                'organization_slug': PRESIDENCY_ORG_SLUG,
                'party_lists_in_use': False,
            }

            org = self.get_or_create_organization(
                election_data['organization_slug'],
                election_data['organization_name'],
            )

            del election_data['organization_name']
            del election_data['organization_slug']
            election_data['organization'] = org

            consistent_data = {
                'candidate_membership_role': 'Candidate',
                'election_date': date(2017, 8, 8),
                'current': True,
                'use_for_candidate_suggestions': False,
                'area_generation': 3,
                'organization': org,
            }

            election_slug = election_data.pop('slug')
            election_data.update(consistent_data)
            election, created = Election.objects.update_or_create(
                slug=election_slug,
                defaults=election_data,
            )

            # Create the AreaType for the country
            # CTR is the Kenya MapIt type for Country
            area_type, created = AreaType.objects.get_or_create(
                name='KECTR',
                defaults={'source': 'MapIt'},
            )

            # Tie the AreaType to the election
            election.area_types.add(area_type)

            # Create the area (only one for the whole country)
            area = self.get_or_create_area(
                identifier='country:1',
                name='Kenya',
                classification='Country',
                area_type=area_type
            )

            # Create and flesh out the actual post
            post = self.get_or_create_post(
                slug=PRESIDENCY_POST_SLUG,
                label=PRESIDENCY_POST_ROLE,
                organization=election.organization,
                area=area,
                role=election.for_post_role,
                election=election,
                party_set=party_set
            )

            errors = check_constraints()
            if errors:
                print errors
                raise Exception('Constraint errors detected. Aborting.')

        # SENATE
        with transaction.atomic():

            # Set up the election
            election_data = {
                'slug': SENATE_ELECTION_SLUG,
                'for_post_role': SENATE_POST_ROLE,
                'name': SENATE_ELECTION_NAME,
                'organization_name': SENATE_ORG_NAME,
                'organization_slug': SENATE_ORG_SLUG,
                'party_lists_in_use': False,
            }

            org = self.get_or_create_organization(
                election_data['organization_slug'],
                election_data['organization_name'],
            )

            del election_data['organization_name']
            del election_data['organization_slug']
            election_data['organization'] = org

            consistent_data = {
                'candidate_membership_role': 'Candidate',
                'election_date': ELECTION_DATE,
                'current': True,
                'use_for_candidate_suggestions': False,
                'area_generation': 3,
                'organization': org,
            }

            election_slug = election_data.pop('slug')
            election_data.update(consistent_data)
            election, created = Election.objects.update_or_create(
                slug=election_slug,
                defaults=election_data,
            )

            # Create the AreaType for the country
            # DIS is the Kenya MapIt type for County/District
            area_type, created = AreaType.objects.get_or_create(
                name='KEDIS',
                defaults={'source': 'MapIt'},
            )

            # Tie the AreaType to the election
            election.area_types.add(area_type)


            # At this point we have the election, organisation and area types ready.
            # Iterate over the senators CSV to build our lists of other things to add.

            counties = {}

            reader = csv.DictReader(open('elections/kenya/data/' + SENATE_CANDIDATES_FILE))
            for row in reader:

                # In this script we only care about the counties, because we're building the posts
                # Actual candidates (and their parties) are done elsewhere

                county_id = row['County Code']

                # Do we already have this county?
                if county_id not in counties:

                    # This is a dict rather than just a name in case we need to easily add anything in future.
                    counties[county_id] = {
                        'id': county_id,
                        'name': row['County Name'].title()
                    }

            # By now counties should contain one of each county.

            # Common stuff
            organization = election.organization
            post_role = election.for_post_role

            # For each county, make sure the area exists and make sure a senate post exists.
            for id, county in counties.iteritems():

                area = self.get_or_create_area(
                    identifier='county:' + county['id'],
                    name=county['name'],
                    classification='County',
                    area_type=area_type
                )

                post_label = SENATE_POST_LABEL_PREFIX + ' ' + county['name']
                post_slug = SENATE_POST_SLUG_PREFIX + '-' + county['id']

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

        # WOMEN REPRESENTATIVES
        with transaction.atomic():

            # Set up the election
            election_data = {
                'slug': WR_ELECTION_SLUG,
                'for_post_role': WR_POST_ROLE,
                'name': WR_ELECTION_NAME,
                'organization_name': ASSEMBLY_ORG_NAME,
                'organization_slug': ASSEMBLY_ORG_SLUG,
                'party_lists_in_use': False,
            }

            org = self.get_or_create_organization(
                election_data['organization_slug'],
                election_data['organization_name'],
            )

            del election_data['organization_name']
            del election_data['organization_slug']
            election_data['organization'] = org

            consistent_data = {
                'candidate_membership_role': 'Candidate',
                'election_date': ELECTION_DATE,
                'current': True,
                'use_for_candidate_suggestions': False,
                'area_generation': 3,
                'organization': org,
            }

            election_slug = election_data.pop('slug')
            election_data.update(consistent_data)
            election, created = Election.objects.update_or_create(
                slug=election_slug,
                defaults=election_data,
            )

            # Create the AreaType for the country
            # DIS is the Kenya MapIt type for County/District
            area_type, created = AreaType.objects.get_or_create(
                name='KEDIS',
                defaults={'source': 'MapIt'},
            )

            # Tie the AreaType to the election
            election.area_types.add(area_type)


            # At this point we have the election, organisation and area types ready.
            # Iterate over the senators CSV to build our lists of other things to add.

            counties = {}

            reader = csv.DictReader(open('elections/kenya/data/' + WR_CANDIDATES_FILE))
            for row in reader:

                # In this script we only care about the counties, because we're building the posts
                # Actual candidates (and their parties) are done elsewhere

                county_id = row['County Code']

                # Do we already have this county?
                if county_id not in counties:

                    # This is a dict rather than just a name in case we need to easily add anything in future.
                    counties[county_id] = {
                        'id': county_id,
                        'name': row['County Name'].title()
                    }

            # By now counties should contain one of each county.

            # Common stuff
            organization = election.organization
            post_role = election.for_post_role

            # For each county, make sure the area exists and make sure a senate post exists.
            for id, county in counties.iteritems():

                area = self.get_or_create_area(
                    identifier='county:' + county['id'],
                    name=county['name'],
                    classification='County',
                    area_type=area_type
                )

                post_label = WR_POST_LABEL_PREFIX + ' ' + county['name']
                post_slug = WR_POST_SLUG_PREFIX + '-' + county['id']

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

        # COUNTY GOVERNORS
        with transaction.atomic():

            # Set up the election
            election_data = {
                'slug': GOV_ELECTION_SLUG,
                'for_post_role': GOV_POST_ROLE,
                'name': GOV_ELECTION_NAME,
                'organization_name': GOV_ORG_NAME,
                'organization_slug': GOV_ORG_SLUG,
                'party_lists_in_use': False,
            }

            org = self.get_or_create_organization(
                election_data['organization_slug'],
                election_data['organization_name'],
            )

            del election_data['organization_name']
            del election_data['organization_slug']
            election_data['organization'] = org

            consistent_data = {
                'candidate_membership_role': 'Candidate',
                'election_date': ELECTION_DATE,
                'current': True,
                'use_for_candidate_suggestions': False,
                'area_generation': 3,
                'organization': org,
            }

            election_slug = election_data.pop('slug')
            election_data.update(consistent_data)
            election, created = Election.objects.update_or_create(
                slug=election_slug,
                defaults=election_data,
            )

            # Create the AreaType for the country
            # DIS is the Kenya MapIt type for County/District
            area_type, created = AreaType.objects.get_or_create(
                name='KEDIS',
                defaults={'source': 'MapIt'},
            )

            # Tie the AreaType to the election
            election.area_types.add(area_type)


            # At this point we have the election, organisation and area types ready.
            # Iterate over the senators CSV to build our lists of other things to add.

            counties = {}

            reader = csv.DictReader(open('elections/kenya/data/' + GOV_CANDIDATES_FILE))
            for row in reader:

                # In this script we only care about the counties, because we're building the posts
                # Actual candidates (and their parties) are done elsewhere

                county_id = row['County Code']

                # Do we already have this county?
                if county_id not in counties:

                    # This is a dict rather than just a name in case we need to easily add anything in future.
                    counties[county_id] = {
                        'id': county_id,
                        'name': row['County Name'].title()
                    }

            # By now counties should contain one of each county.

            # Common stuff
            organization = election.organization
            post_role = election.for_post_role

            # For each county, make sure the area exists and make sure a senate post exists.
            for id, county in counties.iteritems():

                area = self.get_or_create_area(
                    identifier='county:' + county['id'],
                    name=county['name'],
                    classification='County',
                    area_type=area_type
                )

                post_label = GOV_POST_LABEL_PREFIX + ' ' + county['name']
                post_slug = GOV_POST_SLUG_PREFIX + '-' + county['id']

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

        # ASSEMBLY MEMBERS
        with transaction.atomic():

            # Set up the election
            election_data = {
                'slug': ASSEMBLY_ELECTION_SLUG,
                'for_post_role': ASSEMBLY_POST_ROLE,
                'name': ASSEMBLY_ELECTION_NAME,
                'organization_name': ASSEMBLY_ORG_NAME,
                'organization_slug': ASSEMBLY_ORG_SLUG,
                'party_lists_in_use': False,
            }

            org = self.get_or_create_organization(
                election_data['organization_slug'],
                election_data['organization_name'],
            )

            del election_data['organization_name']
            del election_data['organization_slug']
            election_data['organization'] = org

            consistent_data = {
                'candidate_membership_role': 'Candidate',
                'election_date': ELECTION_DATE,
                'current': True,
                'use_for_candidate_suggestions': False,
                'area_generation': 3,
                'organization': org,
            }

            election_slug = election_data.pop('slug')
            election_data.update(consistent_data)
            election, created = Election.objects.update_or_create(
                slug=election_slug,
                defaults=election_data,
            )

            # Create the AreaType for the country
            # CON is the Kenya MapIt type for Constituency
            area_type, created = AreaType.objects.get_or_create(
                name='KECON',
                defaults={'source': 'MapIt'},
            )

            # Tie the AreaType to the election
            election.area_types.add(area_type)


            # At this point we have the election, organisation and area types ready.
            # Iterate over the senators CSV to build our lists of other things to add.

            constituencies = {}

            reader = csv.DictReader(open('elections/kenya/data/' + ASSEMBLY_CANDIDATES_FILE))
            for row in reader:

                # In this script we only care about the constituencies, because we're building the posts
                # Actual candidates (and their parties) are done elsewhere

                constituency_id = row['Constituency Code']

                # Do we already have this constituency?
                if constituency_id not in constituencies:

                    # This is a dict rather than just a name in case we need to easily add anything in future.
                    constituencies[constituency_id] = {
                        'id': constituency_id,
                        'name': row['Constituency Name'].title()
                    }

            # By now constituencies should contain one of each county.

            # Common stuff
            organization = election.organization
            post_role = election.for_post_role

            # For each county, make sure the area exists and make sure a senate post exists.
            for id, constituency in constituencies.iteritems():

                area = self.get_or_create_area(
                    identifier='constituency:' + constituency['id'],
                    name=constituency['name'],
                    classification='Constituency',
                    area_type=area_type
                )

                post_label = ASSEMBLY_POST_LABEL_PREFIX + ' ' + constituency['name']
                post_slug = ASSEMBLY_POST_SLUG_PREFIX + '-' + constituency['id']

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

                consistent_data = {
                    'candidate_membership_role': 'Candidate',
                    'election_date': ELECTION_DATE,
                    'current': True,
                    'use_for_candidate_suggestions': False,
                    'area_generation': 3,
                    'organization': org,
                }

                election_slug = election_data.pop('slug')
                election_data.update(consistent_data)
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
