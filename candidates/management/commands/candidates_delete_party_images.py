from candidates.models import invalidate_cache_entries_from_person_data
from candidates.popit import PopItApiMixin, popit_unwrap_pagination

from django.core.management.base import BaseCommand

class Command(PopItApiMixin, BaseCommand):

    def handle(self, **options):
        for o in popit_unwrap_pagination(
                self.api.organizations,
                per_page=100,
                embed='membership.person'
        ):
            if o['classification'] != 'Party':
                continue
            print o['name']
            for image in o.get('images', []):
                print "  DELETE", image['_id']
                self.api.organizations(o['id']).image(image['_id']).delete()
            # The person pages get party images via the
            # membership.organization embed, so invalidate the cache
            # entries for any person who's a member of this party:
            for membership in o.get('memberships', []):
                invalidate_cache_entries_from_person_data(membership['person_id'])
