from optparse import make_option
from os import chmod, rename
from os.path import dirname
import sys
from tempfile import NamedTemporaryFile

from django.core.management.base import BaseCommand

from candidates.csv_helpers import list_to_csv
from candidates.models import PopItPerson
from candidates.popit import PopItApiMixin, popit_unwrap_pagination


class Command(PopItApiMixin, BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-o', '--output',
                    dest='output_filename',
                    help='The filename to write CSV to'),
        make_option('-y', '--year',
                    dest='year',
                    help='The election year',
                    default='2015'),
    )

    def handle(self, **options):
        all_people = []
        for person_dict in popit_unwrap_pagination(
                self.api.persons,
                embed="membership.organization",
                per_page=100,
        ):
            if person_dict.get('standing_in') \
                and person_dict['standing_in'].get(options['year']):
                person = PopItPerson.create_from_dict(person_dict)
                all_people.append(person.as_dict(year=options['year']))
        csv = list_to_csv(all_people)
        # Write to stdout if no output filename is specified, or if it
        # is '-'
        if options['output_filename'] in (None, '-'):
            with sys.stdout as f:
                f.write(csv)
        else:
            # Otherwise write to a temporary file and atomically
            # rename into place:
            ntf = NamedTemporaryFile(
                delete=False,
                dir=dirname(options['output_filename'])
            )
            ntf.write(csv)
            chmod(ntf.name, 0o644)
            rename(ntf.name, options['output_filename'])
