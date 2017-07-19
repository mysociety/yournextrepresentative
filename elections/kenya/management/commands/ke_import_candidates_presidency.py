# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from candidates.models import (
    AreaExtra, OrganizationExtra, PostExtra, PartySet, PostExtraElection,
)
from elections.models import AreaType, Election
import popolo
from popolo.models import Area, Organization, Post, Person, Membership



import csv
import string
import re

import requests

from candidates.utils import strip_accents


PARTY_SET_SLUG = 'kenya_2017'
ELECTION_SLUG = 'pres-2017'
POST_SLUG = 'president'
CANDIDATES_LIST_FILE = 'candidates_presidency.csv'


class Command(BaseCommand):

    def handle(self, *args, **options):
        with transaction.atomic():

            # Make sure the PartySet exists
            party_set, created = PartySet.objects.get_or_create(slug=PARTY_SET_SLUG)

            # Get the candidates

            reader = csv.DictReader(open('elections/kenya/data/' + CANDIDATES_LIST_FILE))
            for row in reader:

                # No    Surname Other Names Running MateSurname Running Mate Other Names    PartyCode   Political Party Name    Abbrv

                # Assemble a coherent name
                surname = string.capwords(row['Surname'])
                other_names = string.capwords(row['Other Names'])

                name = other_names + ' ' + surname

                # Build an identifier
                id = '-'.join([
                    re.sub('[^\w]*', '', re.sub(r' ', '-', strip_accents(name.lower()))),
                    re.sub('[^\w]*', '', row['Abbrv'].lower())
                ])

                try:
                    person = Person.objects.filter(
                        identifiers__scheme='import-id',
                        identifiers__identifier=id
                    ).get()
                    person.name = name
                except:
                    person = Person.objects.create(
                        name=name
                    )

                    person.identifiers.create(
                        scheme='import-id',
                        identifier=id
                    )

                person.family_name = surname
                person.given_name = other_names

                person.save()

                # Sanity check for the party

                party_name = string.capwords(row['Political Party Name'])
                party_code = string.capwords(row['PartyCode']).lower()

                try:
                    party = Organization.objects.filter(
                        identifiers__scheme='mzalendo-id',
                        identifiers__identifier=party_code
                    ).get()
                    party.name = party_name
                except:
                    party = Organization.objects.create(
                        name=party_name
                    )

                    party.identifiers.create(
                        scheme='mzalendo-id',
                        identifier=party_code
                    )

                party.save()

                # This should be in the party set!
                party_set.parties.add(party)

                # At this point we have a person and a party, so we can go ahead and create a membership

                # First, get the post.
                # Because this is the presidency, there's only the one.
                post = Post.objects.get(extra__slug=POST_SLUG)

                membership = Membership(person=self, post=post, organization=post.organization)
