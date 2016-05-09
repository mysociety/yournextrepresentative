from __future__ import unicode_literals

from collections import defaultdict
from os import chmod, rename
from os.path import dirname
from tempfile import NamedTemporaryFile

from django.core.management.base import BaseCommand, CommandError
from django.db import reset_queries

from candidates.csv_helpers import list_to_csv
from candidates.models import PersonExtra
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

    def handle(self, **options):
        if options['election']:
            try:
                all_elections = [Election.objects.get(slug=options['election'])]
            except Election.DoesNotExist:
                message = "Couldn't find an election with slug {election_slug}"
                raise CommandError(message.format(election_slug=options['election']))
        else:
            all_elections = list(Election.objects.all()) + [None]

        complex_popolo_fields = get_complex_popolo_fields()

        for election in all_elections:
            all_people = []
            if election is None:
                # Get information for every candidate in every
                # election.
                qs = PersonExtra.objects.all()
                for person_extra in queryset_iterator(
                        qs, complex_popolo_fields
                ):
                    all_people += person_extra.as_list_of_dicts(
                        None,
                        base_url=options['site_base_url']
                    )
                output_filename = \
                    options['OUTPUT-PREFIX'] + '-all.csv'
            else:
                # Only get the candidates standing in that particular
                # election
                role = election.candidate_membership_role
                qs = PersonExtra.objects.filter(
                    base__memberships__extra__election=election,
                    base__memberships__role=role,
                )
                for person_extra in queryset_iterator(
                        qs, complex_popolo_fields
                ):
                    all_people += person_extra.as_list_of_dicts(
                        election,
                        base_url=options['site_base_url']
                    )
                output_filename = \
                    options['OUTPUT-PREFIX'] + '-' + election.slug + '.csv'

            group_by_post = election is not None
            csv = list_to_csv(all_people, group_by_post)
            # Write to a temporary file and atomically rename into place:
            ntf = NamedTemporaryFile(
                delete=False,
                dir=dirname(output_filename)
            )
            ntf.write(csv.encode('utf-8'))
            chmod(ntf.name, 0o644)
            rename(ntf.name, output_filename)
