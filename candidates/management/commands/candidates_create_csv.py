from __future__ import unicode_literals

from collections import defaultdict
from os import chmod, rename
from os.path import dirname
from tempfile import NamedTemporaryFile

from django.core.management.base import BaseCommand, CommandError
from django.db import reset_queries

from candidates.csv_helpers import list_to_csv
from candidates.models import PersonExtra, PersonRedirect
from candidates.models.fields import get_complex_popolo_fields
from elections.models import Election


FETCH_AT_A_TIME = 1000


def queryset_iterator(qs, complex_popolo_fields):
    # To save building up a huge list of queries when DEBUG = True,
    # call reset_queries:
    reset_queries()
    start_index = 0
    while True:
        chunk_qs = qs.order_by('pk')[start_index:start_index + FETCH_AT_A_TIME]
        empty = True
        for person_extra in chunk_qs.joins_for_csv_output():
            empty = False
            person_extra.complex_popolo_fields = complex_popolo_fields
            yield person_extra
        if empty:
            return
        start_index += FETCH_AT_A_TIME


def safely_write(output_filename, people, group_by_post):
    csv = list_to_csv(people, group_by_post)
    # Write to a temporary file and atomically rename into place:
    ntf = NamedTemporaryFile(
        delete=False,
        dir=dirname(output_filename)
    )
    ntf.write(csv.encode('utf-8'))
    chmod(ntf.name, 0o644)
    rename(ntf.name, output_filename)


class Command(BaseCommand):

    help = "Output CSV files for all elections"

    def add_arguments(self, parser):
        parser.add_argument(
            'OUTPUT-PREFIX',
            help='The prefix for output filenames'
        )
        parser.add_argument(
            '--site-base-url',
            help='The base URL of the site (for full image URLs)'
        )
        parser.add_argument(
            '--election',
            metavar='ELECTION-SLUG',
            help='Only output CSV for the election with this slug'
        )

    def get_people(self, election, qs):
        all_people = []
        elected_people = []
        for person_extra in queryset_iterator(
                qs, self.complex_popolo_fields
        ):
            for d in person_extra.as_list_of_dicts(
                election,
                base_url=self.options['site_base_url'],
                redirects=self.redirects,
            ):
                all_people.append(d)
                if d['elected'] == 'True':
                    elected_people.append(d)
        return all_people, elected_people

    def handle(self, **options):
        if options['election']:
            try:
                all_elections = [Election.objects.get(slug=options['election'])]
            except Election.DoesNotExist:
                message = "Couldn't find an election with slug {election_slug}"
                raise CommandError(message.format(election_slug=options['election']))
        else:
            all_elections = list(Election.objects.all()) + [None]

        self.options = options
        self.complex_popolo_fields = get_complex_popolo_fields()
        self.redirects = PersonRedirect.all_redirects_dict()

        for election in all_elections:
            if election is None:
                # Get information for every candidate in every
                # election.
                qs = PersonExtra.objects.all()
                all_people, elected_people = self.get_people(election, qs)
                output_filenames = {
                    'all': options['OUTPUT-PREFIX'] + '-all.csv',
                    'elected': options['OUTPUT-PREFIX'] + '-elected-all.csv'
                }
            else:
                # Only get the candidates standing in that particular
                # election
                role = election.candidate_membership_role
                qs = PersonExtra.objects.filter(
                    base__memberships__extra__election=election,
                    base__memberships__role=role,
                )
                all_people, elected_people = self.get_people(election, qs)
                output_filenames = {
                    'all': options['OUTPUT-PREFIX'] + \
                        '-' + election.slug + '.csv',
                    'elected': options['OUTPUT-PREFIX'] +
                        '-elected-' + election.slug + '.csv',
                }
            group_by_post = election is not None
            safely_write(
                output_filenames['all'],
                all_people,
                group_by_post,
            )
            safely_write(
                output_filenames['elected'],
                elected_people,
                group_by_post,
            )
