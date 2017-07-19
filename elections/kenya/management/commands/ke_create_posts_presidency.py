# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from candidates.models import (
    AreaExtra, OrganizationExtra, PostExtra, PartySet, PostExtraElection
)
from elections.models import AreaType, Election
from popolo.models import Area, Organization, Post


PARTY_SET_SLUG = 'kenya_2017'
ELECTION_SLUG = 'pres-2017'
POST_SLUG = 'president'


class Command(BaseCommand):

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

    def handle(self, *args, **options):
        with transaction.atomic():

            # Make sure the PartySet exists
            party_set = PartySet.objects.get_or_create(slug=PARTY_SET_SLUG)

            # Create all the AreaType objects first:
            # CTR is the Kenya MapIt type for Country
            area_type, created = AreaType.objects.get_or_create(
                name='KECTR',
                defaults={'source': 'MapIt'},
            )

            # Set up the election

            election_data = {
                'slug': ELECTION_SLUG,
                'for_post_role': 'President',
                'name': 'Presidential Election 2017',
                'organization_name': 'The Presidency',
                'organization_slug': 'the-presidency',
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
            election.area_types.add(area_type)

            # Create the area (only one for the whole country)

            area, created = Area.objects.update_or_create(
                identifier=1,
                defaults={
                    'name': 'Kenya',
                    'classification': 'Country',
                }
            )
            AreaExtra.objects.update_or_create(
                base=area,
                defaults={'type': area_type}
            )

            # Create the post

            organization = election.organization
            party_set = PartySet.objects.get(slug=PARTY_SET_SLUG)
            post_role = election.for_post_role
            post_label = 'President'
            try:
                post_extra = PostExtra.objects.get(slug=POST_SLUG)
                post = post_extra.base
            except PostExtra.DoesNotExist:
                post = Post.objects.create(
                    label=post_label,
                    organization=organization,
                )
                post_extra = PostExtra.objects.create(
                    base=post,
                    slug=POST_SLUG,
                )
            post.area = area
            post.role = post_role
            post.label = post_label
            post.organization = organization
            post.save()
            post_extra.party_set = party_set
            post_extra.save()
            post_extra.elections.clear()
            PostExtraElection.objects.create(
                postextra=post_extra,
                election=election,
            )
