# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.db import transaction

from candidates.models import (
    AreaExtra, OrganizationExtra, PostExtra, PartySet, PostExtraElection, MembershipExtra, PersonExtra, check_constraints
)
from candidates.views import get_change_metadata
from elections.models import Election
from popolo.models import Organization, Post, Person, Membership

import csv
import re

from candidates.utils import strip_accents


PARTY_SET_SLUG = 'kenya_2017'
PARTY_SET_NAME = 'Register of Politial Parties'

PRESIDENCY_CANDIDATES_FILE = '2017_candidates_presidency.csv'
PRESIDENCY_ELECTION_SLUG = 'pres-2017'
PRESIDENCY_POST_SLUG = 'president'

SENATE_CANDIDATES_FILE = '2017_candidates_senate.csv'
SENATE_ELECTION_SLUG = 'senate-2017'
SENATE_POST_SLUG_PREFIX = 'senator'

WR_CANDIDATES_FILE = '2017_candidates_wr.csv'
WR_ELECTION_SLUG = 'wr-2017'
WR_POST_SLUG_PREFIX = 'wr'

GOV_CANDIDATES_FILE = '2017_candidates_governors.csv'
GOV_ELECTION_SLUG = 'governor-2017'
GOV_POST_SLUG_PREFIX = 'governor'

ASSEMBLY_CANDIDATES_FILE = '2017_candidates_assembly.csv'
ASSEMBLY_ELECTION_SLUG = 'assembly-2017'
ASSEMBLY_POST_SLUG_PREFIX = 'assembly'

WARD_CANDIDATES_FILE = '2017_candidates_county_assemblies.csv'
WARD_ELECTION_SLUG_PREFIX = 'county-assembly-2017'
WARD_POST_SLUG_PREFIX = 'county-assembly'

ELECTIONS = [
    {
        'CANDIDATES_FILE': '2017_candidates_presidency.csv',
        'ROW_TO_ELECTION_SLUG': lambda row: 'pr-2017',
        'ROW_TO_POST_ID': lambda row: 'pr-1',
        'CANDIDATE_ID_PREFIX': 'pr'
    },
    {
        'CANDIDATES_FILE': '2017_candidates_senate.csv',
        'ROW_TO_ELECTION_SLUG': lambda row: 'se-2017',
        'ROW_TO_POST_ID': lambda row: 'se-{0}'.format(row['County Code']),
        'CANDIDATE_ID_PREFIX': 'se'
    },
    {
        'CANDIDATES_FILE': '2017_candidates_wr.csv',
        'ROW_TO_ELECTION_SLUG': lambda row: 'wo-2017',
        'ROW_TO_POST_ID': lambda row: 'wo-{0}'.format(row['County Code']),
        'CANDIDATE_ID_PREFIX': 'wo'
    },
    {
        'CANDIDATES_FILE': '2017_candidates_governors.csv',
        'ROW_TO_ELECTION_SLUG': lambda row: 'go-2017',
        'ROW_TO_POST_ID': lambda row: 'go-{0}'.format(row['County Code']),
        'CANDIDATE_ID_PREFIX': 'go'
    },
    {
        'CANDIDATES_FILE': '2017_candidates_assembly.csv',
        'ROW_TO_ELECTION_SLUG': lambda row: 'na-2017',
        'ROW_TO_POST_ID': lambda row: 'na-{0}'.format(row['Constituency Code']),
        'CANDIDATE_ID_PREFIX': 'na'
    },
    {
        'CANDIDATES_FILE': '2017_candidates_county_assemblies.csv',
        'ROW_TO_ELECTION_SLUG': lambda row: 'co-{0}-2017'.format(row['County Code']),
        'ROW_TO_POST_ID': lambda row: 'co-{0}'.format(row['Ward Code']),
        'CANDIDATE_ID_PREFIX': 'co'
    }
]


class Command(BaseCommand):

    def get_or_create_person(self, scheme, identifier, name, surname, other_names, gender=None):

        try:
            person = Person.objects.get(
                identifiers__scheme=scheme,
                identifiers__identifier=identifier
            )
            person.name = name
        except Person.DoesNotExist:
            person = Person.objects.create(
                name=name
            )

            person.identifiers.create(
                scheme=scheme,
                identifier=identifier
            )

        person.family_name = surname
        person.given_name = other_names

        if gender:
            person.gender = gender

        person.save()

        personExtra, created = PersonExtra.objects.get_or_create(
            base=person,
            defaults={
                'versions': '[]'
            }
        )

        return person

    def get_or_create_party(self, identifier, name, party_set):

        party_slug = 'party:' + identifier

        try:
            party = Organization.objects.get(extra__slug=party_slug)
        except Organization.DoesNotExist:
            party = Organization.objects.create(
                name=name,
                classification='Party'
            )
            partyExtra, created = OrganizationExtra.objects.update_or_create(
                base=party,
                defaults={
                    'slug': party_slug
                }
            )

        # This should be in the party set!
        party_set.parties.add(party)

        return party

    def get_or_create_membership(self, person, post, party, election):

        membership, created = Membership.objects.get_or_create(
            person=person,
            post=post,
            on_behalf_of=party,
            role=election.candidate_membership_role
        )

        # We assume that each membership needs only one Extra object
        membershipExtra, created = MembershipExtra.objects.update_or_create(
            base=membership,
            defaults={
                'election': election,
                'elected': None
            }
        )

        source = "Added from initial import."

        change_metadata = get_change_metadata(None, source)
        person.extra.record_version(change_metadata)
        person.extra.save()

    def import_candidates_for_election(self, election, party_set):

        # Get the candidates
        reader = csv.DictReader(open('elections/kenya/data/' + election['CANDIDATES_FILE']))

        election_objects = {}

        for i, row in enumerate(reader):

            election_slug = election['ROW_TO_ELECTION_SLUG'](row)

            # Make sure the election exists
            election_object = election_objects.get(
                election_slug,
                Election.objects.get(slug=election_slug)
            )

            # Assemble a coherent name
            surname = row['Surname'].title()
            other_names = row['Other Names'].title()

            name = other_names + ' ' + surname

            # Build an identifier
            identifier = '{0}-{1}'.format(election['CANDIDATE_ID_PREFIX'], row['No'])

            person = self.get_or_create_person(
                'iebc-{0}-import-id'.format(election['CANDIDATE_ID_PREFIX']),
                identifier,
                name,
                surname,
                other_names,
                row['Gender'].title()
            )

            # Add the party!
            party = self.get_or_create_party(
                identifier=row['Party Code'],
                name=row['Political Party Name'].title(),
                party_set=party_set
            )

            # At this point we have a person and a party, so we can go ahead and create a membership

            # First, get the post.
            # If this post doesn't exist, we should drop out because someone hasn't run the posts script.
            post_slug = election['ROW_TO_POST_ID'](row)
            post = Post.objects.get(extra__slug=post_slug)

            membership = self.get_or_create_membership(
                person=person,
                post=post,
                party=party,
                election=election_object
            )

            if not (i + 1) % 50:
                print('Imported {}'.format(i + 1))


    @transaction.atomic
    def handle(self, *args, **options):

        # Make sure the PartySet exists
        party_set, created = PartySet.objects.update_or_create(
            slug=PARTY_SET_SLUG,
            defaults={
                'name': PARTY_SET_NAME
            }
        )

        for election in ELECTIONS:
            print('Importing candidates for election: {}'.format(election['CANDIDATES_FILE']))
            self.import_candidates_for_election(election, party_set)

        errors = check_constraints()
        if errors:
            print errors
            raise Exception('Constraint errors detected. Aborting.')
