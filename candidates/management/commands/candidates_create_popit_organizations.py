from django.conf import settings
from django.core.management.base import BaseCommand

from candidates.election_specific import PARTY_DATA
from candidates.models.popit import create_or_update
from candidates.popit import PopItApiMixin

from slumber.exceptions import HttpClientError, HttpServerError

class Command(PopItApiMixin, BaseCommand):
    help = "Create required organizations (parties / chambers) in PopIt"

    def handle(self, **options):

        try:

            # First create all the political parties:

            for party_data in PARTY_DATA.all_party_data:
                create_or_update(
                    self.api.organizations,
                    party_data,
                )

            # Now we create the organizations that all the posts are
            # associated with:

            for election, election_data in settings.ELECTIONS.items():

                create_or_update(
                    self.api.organizations,
                    {
                        'id': election_data['organization_id'],
                        'name': election_data['organization_name'],
                    }
                )

        except (HttpServerError, HttpClientError) as http_error:
            print "The body of the error was:", http_error.content
            raise
