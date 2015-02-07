from django.core.management.base import BaseCommand

from candidates.popit import create_popit_api_object, popit_unwrap_pagination

class Command(BaseCommand):

    def handle(self, *args, **options):
        api = create_popit_api_object()

        for org in popit_unwrap_pagination(
            api.organizations,
            per_page=100
        ):
            org.pop('versions', None)
            org.pop('memberships', None)
            images = org.get('images', [])
            if len(images) < 2:
                continue
            print "====================================================="
            print len(images), org['id'], org['name'].encode('utf-8')
            for image in images:
                print '  --'
                print '   ' + image['notes'].encode('utf-8')
                print '   ' + image['url']
