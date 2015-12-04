from django.core.management.base import BaseCommand, CommandError

from popolo.models import Person

class Command(BaseCommand):

    help = "Add an identifier to a particular person"

    def add_arguments(self, parser):
        parser.add_argument(
            'PERSON-ID',
            help='The ID of the person to add a new identifer for'
        )
        parser.add_argument(
            'SCHEME',
            help='The scheme of the new identifier'
        )
        parser.add_argument(
            'IDENTIFIER',
            help='The identifier to add'
        )

    def handle(self, *args, **options):
        person = Person.objects.get(pk=options['PERSON-ID'])
        person.identifiers.create(
            scheme=options['SCHEME'],
            identifier=options['IDENTIFIER'],
        )

        print "Successfully updated {0}".format(person.name)
