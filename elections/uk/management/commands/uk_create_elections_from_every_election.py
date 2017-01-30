from __future__ import print_function, unicode_literals

import requests

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction


from candidates.models import (
    AreaExtra, OrganizationExtra, PartySet, PostExtra, PostExtraElection
)
from candidates.models import check_paired_models
from elections.models import AreaType, Election
from popolo.models import Area, Organization, Post


class Command(BaseCommand):
    help = 'Create posts and elections from a CSV file at a URL'
    EE_BASE_URL = getattr(
        settings, "EE_BASE_URL", "https://elections.democracyclub.org.uk/")

    @transaction.atomic
    def handle(self, *args, **options):
        # TODO Consider filtering on future or current elections?
        url = "{}api/elections?group_type=organisation".format(
            self.EE_BASE_URL)
        while url:
            req = requests.get(url)
            data = req.json()
            self.process_results(data['results'])
            url = data.get('next')



        errors = check_paired_models()
        if errors:
            for error in errors:
                print(error)
            raise Exception("Unpaired models found - raising" +
                            " an exception to rollback the transaction")

    def process_results(self, results):
        for election in results:
            # TODO Support elections with TMP IDs somehow
            if election.get('election_id'):
                if election.get('group_type') == "organisation":
                    self.process_election(election)

    def process_election(self, election_dict):
        """
        Create the elections
        """
        print(election_dict['election_id'])
        election_model = self.get_election(election_dict)

        organization_extra = self.get_or_create_organisation(
            election_model, election_dict)

        if election_dict['children']:
            for division_id in election_dict['children']:
                self.add_single_division(
                    election_model, organization_extra, division_id)
        else:
            # This is an election to the org directly, with no divisions
            # e.g. a mayor or PCC
            self.add_area(
                election_dict, election_model, organization_extra)

    def get_election(self, election_dict):
        election_id = election_dict['election_id']
        election_date = election_dict['poll_open_date']

        # TODO Set current from the API
        current = True

        return Election.objects.update_or_create(
            slug=election_id,
            election_date=election_date,
            defaults={
                'current': current,
                "name": election_dict['election_title'],
                "for_post_role": election_dict['election_type']['name'],
                "candidate_membership_role": "Candidate",
                "show_official_documents": True,
                "party_lists_in_use":
                    election_dict['voting_system']['uses_party_lists'],
            }
        )[0]

    def add_single_division(self, election_model,
                            organization_extra, division_id):
        url = "{}api/elections/{}".format(
            self.EE_BASE_URL, division_id)
        area_info = requests.get(url).json()

        self.add_area(area_info, election_model, organization_extra)

    def get_or_create_organisation(self, election_model, election_dict):
        org_name = election_dict['organisation']['official_name']
        org_slug = election_dict['organisation']['slug']
        classification = election_dict['organisation']['organisation_type']

        try:
            organization_extra = OrganizationExtra.objects.get(
                slug=org_slug)
            organization = organization_extra.base
        except OrganizationExtra.DoesNotExist:
            organization = Organization.objects.create(
                name=org_name,
                classification=classification
            )
            organization_extra = OrganizationExtra.objects.create(
                base=organization,
                slug=org_slug
            )

        election_model.organization = organization_extra.base
        election_model.save()
        return organization_extra

    def get_party_set(self, territory_code):
        """
        The list of parties used for this election depends on the territory.
        Currently only Northern Ireland uses a different set.
        """
        if territory_code == "NIR":
            partyset_name = "Northern Ireland"
            country = "ni"
        else:
            partyset_name = "Great Britain"
            country = "gb"

        party_set, _ = PartySet.objects.get_or_create(
            slug=country, defaults={'name': partyset_name}
        )
        return party_set

    def get_area_type(self, area_info, election):
        """
        For a single area, normally a code from mapit.mysociety.org like 'UTW'.

        For an organisation, normally the name of the organisation type,
        like 'combined-authority'.

        Organisation types are defined at EE_BASE_URL + /organisations/
        """
        if area_info['division']:
            area_type_name = area_info['division']['division_type']
        else:
            area_type_name = area_info['organisation']['organisation_type']

        area_type, _ = AreaType.objects.update_or_create(
            name=area_type_name,
            defaults={'source': self.EE_BASE_URL}
        )

        if not election.area_types.filter(
                name=area_type.name).exists():
            election.area_types.add(area_type)

        return area_type

    def add_area(self, area_info, election, organization_extra):
        """
        Case 1: An 'area' is the area (like a council ward) that has a ballot
        paper, not necessarily the area of the organisation with an election.

        DC Elections will attach a 'division' to the ballot paper ID that
        relates to the division that was active on the date of the election

        Case 2: When there is a single ballot paper for the organisation, the
        area is that of the the organisation. For example, for a mayoral or PCC
        election.
        """

        party_set = self.get_party_set(
            area_info['organisation']['territory_code'])

        area_type = self.get_area_type(area_info, election)

        if area_info['division']:
            # Case 1, there is an organisational division relted to this
            # area/post
            area_name = area_info['division']['name']
            post_role = area_info['division']['geography_curie']
            post_extra_slug = ":".join([
                area_info['division']['division_type'],
                area_info['division']['geography_curie'].split(':')[-1]
            ])
            area_identifier = area_info['division']['geography_curie']
            winner_count = area_info['division']['seats_total']
        else:
            # Case 2, this organisation isn't split in to divisions for this
            # election, take the info from the organisation directly
            area_name = area_info['organisation']['official_name']
            post_role = area_info['elected_role']
            post_extra_slug = area_info['organisation']['slug']
            area_identifier = ":".join([
                area_info['organisation']['organisation_type'],
                area_info['organisation']['slug'],
            ])
            # TODO this might not always be true, get the count from EE
            winner_count = 1

        area, _ = Area.objects.update_or_create(
            identifier=area_identifier,
            defaults={
                'name': area_name,
            }
        )

        AreaExtra.objects.get_or_create(
            base=area,
            defaults={'type': area_type}
        )

        try:
            post_extra = PostExtra.objects.get(slug=post_extra_slug)
            post = post_extra.base
        except PostExtra.DoesNotExist:
            post = Post.objects.create(
                label=area_name,
                organization=organization_extra.base,
            )
            post_extra = PostExtra.objects.create(
                base=post,
                slug=post_extra_slug,
            )

        post.area = area
        post.role = post_role
        post.label = area_name
        post.organization = organization_extra.base
        post.save()
        post_extra.party_set = party_set
        post_extra.save()

        post_extra.elections.clear()
        PostExtraElection.objects.create(
            postextra=post_extra,
            election=election,
            winner_count=winner_count,
        )
