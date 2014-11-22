from candidates.popit import PopItApiMixin, popit_unwrap_pagination

from django.core.management.base import BaseCommand

class Command(PopItApiMixin, BaseCommand):

    def handle(self, **options):
        max_person_id = -1
        for person in popit_unwrap_pagination(
                self.api.persons,
                per_page=100
        ):
            person_id = int(person['id'])
            max_person_id = max(person_id, max_person_id)
        print "Maximum person ID is:", max_person_id
