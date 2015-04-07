import sys

from candidates.popit import PopItApiMixin, popit_unwrap_pagination
from candidates.update import fix_dates

from django.core.management.base import BaseCommand

from slumber.exceptions import HttpClientError


def strip_bogus_fields(data, bogus_field_keys):
    for key in bogus_field_keys:
        if key in data:
            print "Stripping out", key
            del data[key]


class Command(PopItApiMixin, BaseCommand):

    def handle(self, **options):
        for person in popit_unwrap_pagination(
                self.api.persons,
                embed='',
                per_page=100
        ):
            msg = "Person {0}persons/{1}"
            print msg.format(self.get_base_url(), person['id'])
            strip_bogus_fields(
                person,
                [
                    'founding_date',
                    'dissolution_date',
                    'start_date',
                    'end_date'
                ]
            )
            for image in person.get('images', []):
                strip_bogus_fields(
                    image,
                    [
                        'birth_date',
                        'death_date',
                        'founding_date',
                        'dissolution_date',
                        'start_date',
                        'end_date'
                    ]
                )
            try:
                self.api.persons(person['id']).put(person)
            except HttpClientError as e:
                print "HttpClientError", e.content
                sys.exit(1)
