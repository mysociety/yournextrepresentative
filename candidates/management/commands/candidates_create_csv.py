from __future__ import unicode_literals

from collections import defaultdict
from os import chmod, rename
from os.path import dirname
from tempfile import NamedTemporaryFile

from django.core.management.base import BaseCommand, CommandError

from candidates.csv_helpers import list_to_csv
from candidates.models import PersonExtra
from candidates.models.fields import get_complex_popolo_fields
from elections.models import Election


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
        people_by_election = defaultdict(list)

        complex_popolo_fields = get_complex_popolo_fields()

        for election in all_elections:
            if election is None:
                # Get information for every candidate in every
                # election.
                for person_extra in PersonExtra.objects \
                        .joins_for_csv_output().all():
                    person_extra.complex_popolo_fields = complex_popolo_fields
                    people_by_election[None] += person_extra.as_list_of_dicts(
                        None,
                        base_url=options['site_base_url']
                    )
            else:
                # Only get the candidates standing in that particular
                # election
                role = election.candidate_membership_role
                for person_extra in PersonExtra.objects \
                        .joins_for_csv_output() \
                        .filter(
                            base__memberships__extra__election=election,
                            base__memberships__role=role,
                        ):
                    person_extra.complex_popolo_fields = complex_popolo_fields
                    people_by_election[election.slug] += \
                        person_extra.as_list_of_dicts(
                            election,
                            base_url=options['site_base_url']
                        )

        for election in all_elections:
            if election is None:
                output_filename = \
                    options['OUTPUT-PREFIX'] + '-all.csv'
                election_slug = None
            else:
                output_filename = \
                    options['OUTPUT-PREFIX'] + '-' + election.slug + '.csv'
                election_slug = election.slug
            people_data = people_by_election[election_slug]
            group_by_post = election is not None
            csv = list_to_csv(people_data, group_by_post)
            # Write to a temporary file and atomically rename into place:
            ntf = NamedTemporaryFile(
                delete=False,
                dir=dirname(output_filename)
            )
            ntf.write(csv.encode('utf-8'))
            chmod(ntf.name, 0o644)
            rename(ntf.name, output_filename)
