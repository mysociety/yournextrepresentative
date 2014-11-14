import json
from os import rename
from os.path import dirname
from tempfile import NamedTemporaryFile

from django.core.management.base import LabelCommand

from candidates.popit import create_popit_api_object, popit_unwrap_pagination

class Command(LabelCommand):
    help = "Update JSON dump of the PopIt party data"

    def handle_label(self, output_filename, **options):
        api = create_popit_api_object()
        ntf = NamedTemporaryFile(
            delete=False,
            dir=dirname(output_filename)
        )
        all_parties = []
        for party in popit_unwrap_pagination(api.organizations, embed=''):
            if party['classification'] != 'Party':
                continue
            party.pop('image', None)
            party.pop('images', None)
            all_parties.append(party)
        json.dump(all_parties, ntf, sort_keys=True, indent=4)
        rename(ntf.name, output_filename)
