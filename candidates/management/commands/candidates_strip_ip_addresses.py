from candidates.popit import PopItApiMixin, popit_unwrap_pagination

from django.core.management.base import BaseCommand

class Command(PopItApiMixin, BaseCommand):

    def handle(self, **options):
        for person in popit_unwrap_pagination(
                self.api.persons,
                per_page=100
        ):
            print u"Stripping IP addresses from {name} ({id})".format(
                **person
            ).encode('utf-8')
            for version in person.get('versions', []):
                version.pop('ip', None)
            self.api.persons(person['id']).put(person)
