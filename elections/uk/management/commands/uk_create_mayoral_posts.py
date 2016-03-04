from __future__ import print_function, unicode_literals

from datetime import date

from django.core.management.base import BaseCommand

from candidates.models import (
    AreaExtra, OrganizationExtra, PartySet, PostExtra, PostExtraElection
)
from elections.models import AreaType, Election
from popolo.models import Area, Organization, Post


class Command(BaseCommand):
    help = 'Create posts and elections for the 2016 PCC elections'

    def handle(self, **options):
        self.gb_parties, _ = PartySet.objects.get_or_create(
            slug='gb', defaults={'name': 'Great Britain'}
        )

        self.elections = {
            'mayor.bristol.2016-05-05': {
                'area_generation': 1,
                'area_id': 'gss:E06000023',
                'area_name': 'Bristol City Council',
                'area_type': 'UTA',
                'election_date': date(2016, 5, 5),
                'for_post_role': 'Mayor',
                'label_format': 'Mayor of Bristol',
                'name': 'Bristol Mayoral Election',
                'organisation_name': 'Bristol Council',
                'organisation_slug': 'bristol-council',
                'party_lists_in_use': False,
                'post_slug': 'mayor:bristol',
            },
            'mayor.liverpool.2016-05-05': {
                'area_generation': 1,
                'area_id': 'gss:E08000012',
                'area_name': 'Liverpool City Council',
                'area_type': 'MTD',
                'election_date': date(2016, 5, 5),
                'for_post_role': 'Mayor',
                'label_format': 'Mayor of Liverpool',
                'name': 'Liverpool Mayoral Election',
                'organisation_name': 'Liverpool Council',
                'organisation_slug': 'liverpool-council',
                'party_lists_in_use': False,
                'post_slug': 'mayor:liverpool',
            },
            'mayor.london.2016-05-05': {
                'area_generation': 1,
                'area_id': 'unit_id:41441',
                'area_name': 'Greater London Authority',
                'area_type': 'GLA',
                'election_date': date(2016, 5, 5),
                'for_post_role': 'Mayor',
                'label_format': 'Mayor of London',
                'name': 'London Mayoral Election',
                'organisation_name': 'Greater London Authority',
                'organisation_slug': 'gla',
                'party_lists_in_use': False,
                'post_slug': 'mayor:london',
            },
            'mayor.salford.2016-05-05': {
                'area_generation': 1,
                'area_id': 'gss:E08000006',
                'area_name': 'Salford City Council',
                'area_type': 'MTD',
                'election_date': date(2016, 5, 5),
                'for_post_role': 'Mayor',
                'label_format': 'Mayor of Salford',
                'name': 'Salford Mayoral Election',
                'organisation_name': 'Salford Council',
                'organisation_slug': 'salford-council',
                'party_lists_in_use': False,
                'post_slug': 'mayor:salford',
            },

        }

        for election_id, election in self.elections.items():
            election['organisation_object'] = \
                self.create_organisation(election_id, election)
            election['election_object'] =\
                self.create_election(election_id, election)
            self.add_area(election_id, election)

    def create_organisation(self, election_id, election):
        org_name = election['organisation_name']
        org_slug = election['organisation_slug']

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
            k: election[k] for k in [
                'name', 'for_post_role', 'area_generation', 'election_date',
                'party_lists_in_use']
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

    def add_area(self, election_id, election):

        area_type, _ = AreaType.objects.update_or_create(
            name=election['area_type'],
            defaults={'source': 'MapIt'}
        )

        if not election['election_object'].area_types.filter(
                name=area_type.name).exists():
            election['election_object'].area_types.add(area_type)

        area, _ = Area.objects.update_or_create(
            identifier=election['area_id'],
            defaults={'name': election['area_name']}
        )

        AreaExtra.objects.get_or_create(base=area, type=area_type)

        post, _ = Post.objects.update_or_create(
            organization=election['organisation_object'].base,
            area=area,
            role=election['for_post_role'],
            defaults={
                'label': election['label_format']
            })
        post_extra, _ = PostExtra.objects.update_or_create(
            base=post,
            defaults={
                'slug': election['post_slug'],
                'party_set': self.gb_parties,
            },
        )
        PostExtraElection.objects.update_or_create(
            postextra=post_extra,
            election=election['election_object'],
        )
