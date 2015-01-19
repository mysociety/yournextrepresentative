from candidates.popit import PopItApiMixin, popit_unwrap_pagination

from django.core.management.base import BaseCommand

class Command(PopItApiMixin, BaseCommand):

    def handle(self, **options):
        for o in popit_unwrap_pagination(
                self.api.organizations,
                per_page=100
        ):
            if o['classification'] != 'Party':
                continue
            print o['name']
            for image in o.get('images', []):
                print "  DELETE", image['_id']
                self.api.organizations(o['id']).image(image['_id']).delete()
