from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from candidates.popit import create_popit_api_object
from candidates.update import PersonParseMixin, PersonUpdateMixin
from candidates.views import CandidacyMixin

from slumber.exceptions import HttpClientError, HttpServerError

class Command(PersonParseMixin, PersonUpdateMixin, CandidacyMixin, BaseCommand):
    args = "<PERSON-ID> <OTHER-NAME>"
    help = "Add an alternative name to a particular person"

    option_list = BaseCommand.option_list + (
        make_option('--note', dest='note', help='A note about this other name'),
        make_option('--start-date', help='When this alternative name began being used'),
        make_option('--end-date', help='When this alternative name stopped being used'),
    )

    def handle(self, *args, **options):
        self.verbosity = int(options.get('verbosity', 1))
        popit = create_popit_api_object()
        if len(args) != 2:
            raise CommandError("You must provide all two arguments")

        person_id, other_name = args

        try:
            person_data = popit.persons(person_id).get()['result']
        except (HttpClientError, HttpServerError):
            message = "Failed to get the person with ID {0}"
            raise CommandError(message.format(person_id))

        person_data['other_names'].append(
            {
                'name': other_name,
                'note': options['note'],
                'start_date': options['start_date'],
                'end_date': options['end_date']
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
