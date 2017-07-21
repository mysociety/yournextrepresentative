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
import string
import re

from candidates.utils import strip_accents


PARTY_SET_SLUG = 'kenya_2017'

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


class Command(BaseCommand):

    def get_or_create_person(self, scheme, identifier, name, surname, other_names):

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

    def handle(self, *args, **options):

        # Make sure the PartySet exists
        party_set, created = PartySet.objects.get_or_create(slug=PARTY_SET_SLUG)

        # PRESIDENCY
        with transaction.atomic():

            # Make sure the election exists
            election = Election.objects.get(slug=PRESIDENCY_ELECTION_SLUG)

            # Get the candidates

            reader = csv.DictReader(open('elections/kenya/data/' + PRESIDENCY_CANDIDATES_FILE))
            for row in reader:

                # Assemble a coherent name
                surname = string.capwords(row['Surname'])
                other_names = string.capwords(row['Other Names'])

                name = other_names + ' ' + surname

                # Build an identifier
                id = '-'.join([
                    re.sub('[^\w]*', '', re.sub(r' ', '-', strip_accents(name.lower()))),
                    re.sub('[^\w]*', '', row['Abbrv'].lower())
                ])

                person = self.get_or_create_person(
                    'mz-presidency-import-id',
                    id,
                    name,
                    surname,
                    other_names
                )

                # Add the party!
                party = self.get_or_create_party(
                    identifier=row['PartyCode'],
                    name=string.capwords(row['Political Party Name']),
                    party_set=party_set
                )

                # At this point we have a person and a party, so we can go ahead and create a membership

                # First, get the post.
                # Because this is the presidency, there's only the one.
                # If this post doesn't exist, we should drop out because someone hasn't run the posts script.
                post = Post.objects.get(extra__slug=PRESIDENCY_POST_SLUG)

                membership = self.get_or_create_membership(
                    person=person,
                    post=post,
                    party=party,
                    election=election
                )

            errors = check_constraints()
            if errors:
                print errors
                raise Exception('Constraint errors detected. Aborting.')

        # SENATE
        with transaction.atomic():

            # Make sure the election exists
            election = Election.objects.get(slug=SENATE_ELECTION_SLUG)

            # Get the candidates

            reader = csv.DictReader(open('elections/kenya/data/' + SENATE_CANDIDATES_FILE))
            for row in reader:

                # Assemble a coherent name
                surname = string.capwords(row['Surname'])
                other_names = string.capwords(row['Other Names'])

                name = other_names + ' ' + surname

                # Build an identifier
                id = '-'.join([
                    re.sub('[^\w]*', '', re.sub(r' ', '-', strip_accents(name.lower()))),
                    re.sub('[^\w]*', '', row['Abbrv'].lower())
                ])

                person = self.get_or_create_person(
                    'mz-senate-import-id',
                    id,
                    name,
                    surname,
                    other_names
                )

                # Add the party!
                party = self.get_or_create_party(
                    identifier=row['Party Code'],
                    name=string.capwords(row['Political Party Name']),
                    party_set=party_set
                )

                # At this point we have a person and a party, so we can go ahead and create a membership

                # First, get the post.
                # If this post doesn't exist, we should drop out because someone hasn't run the posts script.
                post = Post.objects.get(extra__slug=SENATE_POST_SLUG_PREFIX + '-' + row['County Code'])

                membership = self.get_or_create_membership(
                    person=person,
                    post=post,
                    party=party,
                    election=election
                )

            errors = check_constraints()
            if errors:
                print errors
                raise Exception('Constraint errors detected. Aborting.')

        # WOMEN REPRESENTATIVES
        with transaction.atomic():

            # Make sure the election exists
            election = Election.objects.get(slug=WR_ELECTION_SLUG)

            # Get the candidates

            reader = csv.DictReader(open('elections/kenya/data/' + WR_CANDIDATES_FILE))
            for row in reader:

                # Assemble a coherent name
                surname = string.capwords(row['Surname'])
                other_names = string.capwords(row['Other Names'])

                name = other_names + ' ' + surname

                # Build an identifier
                id = '-'.join([
                    re.sub('[^\w]*', '', re.sub(r' ', '-', strip_accents(name.lower()))),
                    re.sub('[^\w]*', '', row['Abbrv'].lower())
                ])

                person = self.get_or_create_person(
                    'mz-wr-import-id',
                    id,
                    name,
                    surname,
                    other_names
                )

                # Add the party!
                party = self.get_or_create_party(
                    identifier=row['Party Code'],
                    name=string.capwords(row['Political Party Name']),
                    party_set=party_set
                )

                # At this point we have a person and a party, so we can go ahead and create a membership

                # First, get the post.
                # If this post doesn't exist, we should drop out because someone hasn't run the posts script.
                post = Post.objects.get(extra__slug=WR_POST_SLUG_PREFIX + '-' + row['County Code'])

                membership = self.get_or_create_membership(
                    person=person,
                    post=post,
                    party=party,
                    election=election
                )

            errors = check_constraints()
            if errors:
                print errors
                raise Exception('Constraint errors detected. Aborting.')

        # COUNTY GOVERNORS
        with transaction.atomic():

            # Make sure the election exists
            election = Election.objects.get(slug=GOV_ELECTION_SLUG)

            # Get the candidates

            reader = csv.DictReader(open('elections/kenya/data/' + GOV_CANDIDATES_FILE))
            for row in reader:

                # Assemble a coherent name
                surname = string.capwords(row['Surname'])
                other_names = string.capwords(row['Other Names'])

                name = other_names + ' ' + surname

                # Build an identifier
                id = '-'.join([
                    re.sub('[^\w]*', '', re.sub(r' ', '-', strip_accents(name.lower()))),
                    re.sub('[^\w]*', '', row['Abbrv'].lower())
                ])

                person = self.get_or_create_person(
                    'mz-gov-import-id',
                    id,
                    name,
                    surname,
                    other_names
                )

                # Add the party!
                party = self.get_or_create_party(
                    identifier=row['Party Code'],
                    name=string.capwords(row['Political Party Name']),
                    party_set=party_set
                )

                # At this point we have a person and a party, so we can go ahead and create a membership

                # First, get the post.
                # If this post doesn't exist, we should drop out because someone hasn't run the posts script.
                post = Post.objects.get(extra__slug=GOV_POST_SLUG_PREFIX + '-' + row['County Code'])

                membership = self.get_or_create_membership(
                    person=person,
                    post=post,
                    party=party,
                    election=election
                )

            errors = check_constraints()
            if errors:
                print errors
                raise Exception('Constraint errors detected. Aborting.')

        # ASSEMBLY MEMBERS
        with transaction.atomic():

            # Make sure the election exists
            election = Election.objects.get(slug=ASSEMBLY_ELECTION_SLUG)

            # Get the candidates

            reader = csv.DictReader(open('elections/kenya/data/' + ASSEMBLY_CANDIDATES_FILE))
            for row in reader:

                # Assemble a coherent name
                surname = string.capwords(row['Surname'])
                other_names = string.capwords(row['Other Names'])

                name = other_names + ' ' + surname

                # Build an identifier
                id = '-'.join([
                    re.sub('[^\w]*', '', re.sub(r' ', '-', strip_accents(name.lower()))),
                    re.sub('[^\w]*', '', row['Abbrv'].lower())
                ])

                person = self.get_or_create_person(
                    'mz-assembly-import-id',
                    id,
                    name,
                    surname,
                    other_names
                )

                # Add the party!
                party = self.get_or_create_party(
                    identifier=row['Party Code'],
                    name=string.capwords(row['Political Party Name']),
                    party_set=party_set
                )

                # At this point we have a person and a party, so we can go ahead and create a membership

                # First, get the post.
                # If this post doesn't exist, we should drop out because someone hasn't run the posts script.
                post = Post.objects.get(extra__slug=ASSEMBLY_POST_SLUG_PREFIX + '-' + row['Constituency Code'])

                membership = self.get_or_create_membership(
                    person=person,
                    post=post,
                    party=party,
                    election=election
                )

            errors = check_constraints()
            if errors:
                print errors
                raise Exception('Constraint errors detected. Aborting.')
