# From (I believe) historical bugs, some candidates are missing PopIt
# memberships.  This command will recreate them based on their
# standing_in and party_memberships data.
#
#   e.g. ./manage.py candidates_recreate_memberships 2825 3411

from django.core.management.base import BaseCommand, CommandError

from candidates.models import PopItPerson
from candidates.popit import create_popit_api_object
from candidates.update import PersonUpdateMixin

class Command(PersonUpdateMixin, BaseCommand):

    args = "<PERSON-ID> ..."
    help = "Recreate one or more person's memberships (for fixing bad data)"

    def handle(self, *args, **kwargs):
        if len(args) < 1:
            raise CommandError("You must provide one or more PopIt person ID")
        for person_id in args:
            person = PopItPerson.create_from_popit(
                create_popit_api_object(), person_id
            )
            person.delete_memberships()
            self.create_party_memberships(person_id, person.popit_data)
            self.create_candidate_list_memberships(person_id, person.popit_data)
