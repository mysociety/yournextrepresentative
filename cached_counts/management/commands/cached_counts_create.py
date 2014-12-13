from collections import defaultdict
import json

from candidates.popit import PopItApiMixin, popit_unwrap_pagination
from candidates.static_data import MapItData, PartyData

from django.core.management.base import BaseCommand

from cached_counts.models import CachedCount

class Command(PopItApiMixin, BaseCommand):

    def add_or_update(self, obj):
        c, created = CachedCount.objects.get_or_create(
            object_id=obj['object_id'], count_type=obj['count_type'],
            defaults={'count': obj['count'], 'name': obj['name']})
        if not created:
            c.count = obj['count']
            c.name = obj['name']
            c.save()

    def handle(self, **options):
        all_constituencies = MapItData.constituencies_2010_name_sorted
        all_parties = PartyData.party_id_to_name
        counts = {
            'candidates_2015': 0,
            'parties': {name: {'count': 0, 'party_id': party_id}
                        for party_id, name in all_parties.items()},
            'constituencies': {n[1]['name']: {'count': 0, 'con_id':n[1]['id']}
                                for n in all_constituencies},
        }

        # Loop over everything, counting things we're interseted in
        for person in popit_unwrap_pagination(
                self.api.persons,
                embed="membership.organization",
                per_page=100
        ):
            if person.get('standing_in') and person['standing_in'].get('2015'):
                counts['candidates_2015'] += 1

                party_name = person['party_memberships']['2015']['name']
                counts['parties'][party_name]['count'] += 1

                constituency_name = person['standing_in']['2015']['name']
                counts['constituencies'][constituency_name]['count'] += 1

        # Add or create objects in the database
        # Parties
        for party_name, data in counts['parties'].items():
            obj = {
                'count_type': 'party',
                'name': party_name,
                'count': data['count'],
                'object_id': data['party_id']

            }

            self.add_or_update(obj)

        # Constituencies
        for constituency_name, data in counts['constituencies'].items():
            obj = {
                'count_type': 'constituency',
                'name': constituency_name,
                'count': data['count'],
                'object_id': data['con_id']

            }

            self.add_or_update(obj)

        obj = {
            'count_type': 'total',
            'name': 'total_2015',
            'count': counts['candidates_2015'],
            'object_id': 'candidates_2015',
        }
        self.add_or_update(obj)
