from candidates.popit import PopItApiMixin, popit_unwrap_pagination

from django.core.management.base import BaseCommand

class Command(PopItApiMixin, BaseCommand):

    def handle(self, **options):
        for person in popit_unwrap_pagination(
                self.api.persons,
                per_page=100
        ):
            print person['url']
            for m in person.get('memberships', []):
                if m.get('role', '') == 'Candidate' and not m.get('post_id'):
                    print u'Person {0} ({1}) is missing a post_id on membership {2}'.format(
                        person['name'], person['id'], m['id']
                    ).encode('utf-8')
