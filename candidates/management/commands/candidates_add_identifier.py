from django.core.management.base import BaseCommand, CommandError

from candidates.popit import create_popit_api_object
from candidates.update import PersonParseMixin, PersonUpdateMixin
from candidates.views import CandidacyMixin

from slumber.exceptions import HttpClientError, HttpServerError

class Command(PersonParseMixin, PersonUpdateMixin, CandidacyMixin, BaseCommand):
    args = "<PERSON-ID> <SCHEME> <IDENTIFIER>"
    help = "Add an identifier to a particular person"

    def handle(self, *args, **options):
        self.verbosity = int(options.get('verbosity', 1))
        popit = create_popit_api_object()
        if len(args) != 3:
            raise CommandError("You must provide all three arguments")

        person_id, scheme, identifier = args

        try:
            person_data = popit.persons(person_id).get()['result']
        except (HttpClientError, HttpServerError):
            message = "Failed to get the person with ID {0}"
            raise CommandError(message.format(person_id))

        person_data['identifiers'].append(
            {
                'scheme': scheme,
                'identifier': identifier,
            }
        )

        try:
            popit.persons(person_id).put(person_data)
        except (HttpClientError, HttpServerError):
            raise CommandError("Failed to update that person")

        # FIXME: this should create a new version in the versions
        # array too, otherwise you manually have to edit on YourNextMP
        # too to create a new version with a change message.

        print "Successfully updated {0}".format(person_id)
