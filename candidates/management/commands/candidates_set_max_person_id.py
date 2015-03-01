from candidates.popit import PopItApiMixin, popit_unwrap_pagination

from django.core.management.base import BaseCommand

from candidates.models import MaxPopItIds

class Command(PopItApiMixin, BaseCommand):

    def handle(self, **options):
        print "Finding the maximum person ID from PopIt"
        max_person_id = -1
        for person in popit_unwrap_pagination(
                self.api.persons,
                per_page=100
        ):
            person_id = int(person['id'])
            max_person_id = max(person_id, max_person_id)
        print "Setting maximum PopIt person ID to:", max_person_id
        MaxPopItIds.update_max_persons_id(max_person_id)
