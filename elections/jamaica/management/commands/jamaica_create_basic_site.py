# -*- coding: utf-8 -*-

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from candidates.models import (
    AreaExtra, OrganizationExtra, PostExtra, PartySet, PostExtraElection
)
from elections.models import AreaType, Election
from popolo.models import Area, Organization, Post


class Command(BaseCommand):

    PARTIES = [
        u"People's National Party",
        u"Jamaica Labour Party",
        u"National Democratic Movement",
        u"Marcus Garvey People's Progressive Party",
        u"People's Progressive Party",
        u"Hope Party",
        u"Independent",
    ]

    AREAS = [
        u'Clarendon Central',
        u'Clarendon North Central',
        u'Clarendon North Western',
        u'Clarendon Northern',
        u'Clarendon South Eastern',
        u'Clarendon South Western',
        u'Hanover Eastern',
        u'Hanover Western',
        u'Kingston Central',
        u'Kingston East and Port Royal',
        u'Kingston Western',
        u'Manchester Central',
        u'Manchester North Eastern',
        u'Manchester North Western',
        u'Manchester Southern',
        u'Portland Eastern',
        u'Portland Western',
        u'St. Andrew East Central',
        u'St. Andrew Eastern',
        u'St. Andrew East Rural',
        u'St. Andrew North Central',
        u'St. Andrew North Eastern',
        u'St. Andrew North Western',
        u'St. Andrew South Eastern',
        u'St. Andrew South Western',
        u'St. Andrew Southern',
        u'St. Andrew West Central',
        u'St. Andrew West Rural',
        u'St. Andrew Western',
        u'St. Ann North Eastern',
        u'St. Ann North Western',
        u'St. Ann South Eastern',
        u'St. Ann South Western',
        u'St. Catherine Central',
        u'St. Catherine East Central',
        u'St. Catherine Eastern',
        u'St. Catherine North Central',
        u'St. Catherine North Eastern',
        u'St. Catherine North Western',
        u'St. Catherine South Central',
        u'St. Catherine South Eastern',
        u'St. Catherine South Western',
        u'St. Catherine Southern',
        u'St. Catherine West Central',
        u'St. Elizabeth North Eastern',
        u'St. Elizabeth North Western',
        u'St. Elizabeth South Eastern',
        u'St. Elizabeth South Western',
        u'St. James Central',
        u'St. James East Central',
        u'St. James North Western',
        u'St. James Southern',
        u'St. James West Central',
        u'St. Mary Central',
        u'St. Mary South Eastern',
        u'St. Mary Western',
        u'St. Thomas Eastern',
        u'St. Thomas Western',
        u'Trelawny Northern',
        u'Trelawny South',
        u'Westmoreland Central',
        u'Westmoreland Eastern',
        u'Westmoreland Western'
    ]

    def get_or_create_organization(self, slug, name, classification=None):
        try:
            org_extra = OrganizationExtra.objects.get(slug=slug)
            org = org_extra.base
            org.name = name
            if classification is not None:
                org.classification = classification
            org.save()
        except OrganizationExtra.DoesNotExist:
            org = Organization.objects.create(name=name)
            org_extra = OrganizationExtra.objects.create(base=org, slug=slug)
        return org

    def get_party_set(self, cons_name):
        party_set_slug = "2016_cons_{0}".format(slugify(cons_name))
        party_set_name = u"2016 parties in {0}".format(cons_name)
        try:
            return PartySet.objects.get(slug=party_set_slug)
        except PartySet.DoesNotExist:
            # self.stdout.write("Couldn't find the party set '{0}'".format(
                # party_set_slug
            # ))
            return PartySet.objects.create(
                slug=party_set_slug, name=party_set_name
            )

    def handle(self, *args, **options):
        with transaction.atomic():
            # Create all the AreaType objects first:
            area_type, created = AreaType.objects.get_or_create(
                name='JAMAICACONS',
                defaults={'source': 'MapIt'},
            )
            # Now the Election objects (and the organizations they're
            # associated with)
            elections = []
            for election_data in [
                    {
                        'slug': 'representatives-2016',
                        'for_post_role': 'Member of Parliament',
                        'name': u'House of Representatives 2016',
                        'organization_name': u'House of Representatives',
                        'organization_slug': 'house-of-representatives',
                        'party_lists_in_use': False,
                    },
            ]:
                org = self.get_or_create_organization(
                    election_data['organization_slug'],
                    election_data['organization_name'],
                )
                del election_data['organization_name']
                del election_data['organization_slug']
                election_data['organization'] = org
                consistent_data = {
                    'candidate_membership_role': 'Candidate',
                    'election_date': date(2016, 2, 7),
                    'current': True,
                    'use_for_candidate_suggestions': False,
                    'area_generation': 2,
                    'organization': org,
                }
                election_slug = election_data.pop('slug')
                election_data.update(consistent_data)
                election, created = Election.objects.update_or_create(
                    slug=election_slug,
                    defaults=election_data,
                )
                election.area_types.add(area_type)
                elections.append(election)

            party_set = self.get_party_set(elections[0].name)

            # Now create all the Area objects:
            areas = []
            count = 1
            for area_name in self.AREAS:
                for party_name in self.PARTIES:
                    slug = slugify(party_name)
                    party = self.get_or_create_organization(slug, party_name, 'Party')
                    if not party.party_sets.filter(slug=party_set.slug):
                        # print "adding party set {0}".format(party_set.slug)
                        party.party_sets.add(party_set)

                area, created = Area.objects.update_or_create(
                    identifier=count,
                    defaults={
                        'name': area_name,
                        'classification': 'Constituency',
                    }
                )
                count += 1
                AreaExtra.objects.update_or_create(
                    base=area,
                    defaults={'type': area_type}
                )
                areas.append(area)
            # Now create all the Post objects:
            for election in elections:
                for area in areas:
                    organization = election.organization
                    post_role = election.for_post_role
                    post_label = u'Member of Parliament for {0}' \
                        .format(area.name)
                    post_slug = 'cons-' + str(area.identifier)
                    try:
                        post_extra = PostExtra.objects.get(slug=post_slug)
                        post = post_extra.base
                    except PostExtra.DoesNotExist:
                        post = Post.objects.create(
                            label=post_label,
                            organization=organization,
                        )
                        post_extra = PostExtra.objects.create(
                            base=post,
                            slug=post_slug,
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
