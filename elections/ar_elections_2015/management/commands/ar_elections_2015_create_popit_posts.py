import json

from django.core.management.base import BaseCommand
from django.conf import settings

from candidates.models.popit import create_or_update
from candidates.popit import PopItApiMixin
from candidates.static_data import MapItData

from slumber.exceptions import HttpServerError, HttpClientError

class Command(PopItApiMixin, BaseCommand):
    help = "Create the posts for the 2015 elections in Argentina"

    def handle_mapit_type(self, election, election_data, mapit_type):
        mapit_tuple = (mapit_type, election_data['mapit_generation'])
        for id, area in MapItData.areas_by_id[mapit_tuple].items():
            post_id = election_data['get_post_id'](
                mapit_type, id
            )
            role = election_data['for_post_role']
            post_data = {
                'role': role,
                'id': post_id,
                'label': role + u' por ' + area['name'],
            }
            create_or_update(self.api.posts, post_data)

    def handle(self, **options):
        try:
            for election, election_data in settings.ELECTIONS.items():
                if election == 'presidentes-argentina-paso-2015':
                    create_or_update(
                        self.api.posts,
                        {
                            'id': 'presidente',
                            'label': 'Candidato a Presidente',
                            'role': 'Candidato a Presidente',
                        }
                    )
                else:
                    for mapit_type in election_data['mapit_types']:
                        self.handle_mapit_type(election, election_data, mapit_type)
        except (HttpServerError, HttpClientError) as hse:
            print "The body of the error was:", hse.content
            raise
