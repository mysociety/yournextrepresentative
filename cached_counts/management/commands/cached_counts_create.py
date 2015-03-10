from candidates.popit import PopItApiMixin, popit_unwrap_pagination
from candidates.static_data import MapItData, PartyData

from django.core.management.base import BaseCommand

from cached_counts.models import CachedCount

class Command(PopItApiMixin, BaseCommand):

    def add_or_update(self, obj):
        CachedCount.objects.update_or_create(
            object_id=obj['object_id'], count_type=obj['count_type'],
            defaults={'count': obj['count'], 'name': obj['name']})

    def handle(self, **options):
        all_constituencies = MapItData.constituencies_2010_name_sorted
        all_parties = PartyData.party_id_to_name
        counts = {
            'candidates_2010': 0,
            'candidates_2015': 0,
            'parties': {party_id: {'count': 0, 'party_name': name}
                        for party_id, name in all_parties.items()},
            'constituencies': {n[1]['name']: {'count': 0, 'con_id':n[1]['id']}
                                for n in all_constituencies},
        }
        standing_again_same_party = 0
        standing_again_different_party = 0
        all_people = 0
        new_candidates = 0
        # Loop over everything, counting things we're interseted in
        for person in popit_unwrap_pagination(
                self.api.persons,
                embed="membership.organization",
                per_page=100
        ):
            all_people += 1
            if not person.get('standing_in'):
                continue
            if person['standing_in'].get('2010'):
                counts['candidates_2010'] += 1
            if person['standing_in'].get('2015'):
                counts['candidates_2015'] += 1
                party_id = person['party_memberships']['2015']['id']
                counts['parties'][party_id]['count'] += 1
                constituency_name = person['standing_in']['2015']['name']
                counts['constituencies'][constituency_name]['count'] += 1
                if person['standing_in'].get('2010'):
                    if party_id == person['party_memberships']['2010']['id']:
                        standing_again_same_party += 1
                    else:
                        standing_again_different_party += 1
                else:
                    new_candidates += 1

        # Add or create objects in the database
        # Parties
        for party_id, data in counts['parties'].items():
            obj = {
                'count_type': 'party',
                'name': data['party_name'],
                'count': data['count'],
                'object_id': party_id

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

        for name, count, object_id in (
            ('new_candidates', new_candidates, 'new_candidates'),
            ('total_2010', counts['candidates_2010'], 'candidates_2010'),
            ('total_2015', counts['candidates_2015'], 'candidates_2015'),
            ('standing_again_same_party',
             standing_again_same_party,
             'standing_again_same_party'),
            ('standing_again_different_party',
             standing_again_different_party,
             'standing_again_different_party'),
            ('standing_again',
             standing_again_same_party + standing_again_different_party,
             'standing_again'),
        ):
            obj = {
                'count_type': 'total',
                'name': name,
                'count': count,
                'object_id': object_id,
            }
            self.add_or_update(obj)
