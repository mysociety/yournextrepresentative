from candidates.popit import PopItApiMixin, popit_unwrap_pagination
from candidates.models import PopItPerson

from django.core.management.base import BaseCommand

from candidates.csv_helpers import list_to_csv


class Command(PopItApiMixin, BaseCommand):
    def handle(self, **options):
        all_people = []
        for person_dict in popit_unwrap_pagination(
                self.api.persons,
                embed="membership.organization",
                per_page=100,
        ):
            if person_dict.get('standing_in') \
                and person_dict['standing_in'].get('2015'):
                person = PopItPerson.create_from_dict(self.api,
                    person_dict['id'])
                all_people.append(person.as_list)
        # Output final file
        list_to_csv(all_people)
