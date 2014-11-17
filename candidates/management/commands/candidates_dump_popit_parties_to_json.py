import json
from os import rename
from os.path import dirname
import re
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
        for party in popit_unwrap_pagination(
                api.organizations,
                embed='',
                per_page=200
        ):
            if party['classification'] != 'Party':
                continue
            party.pop('image', None)
            party.pop('images', None)
            # The generated id in each identifier will be different
            # between systems (or between runs on the same system) so
            # just produces noisy diffs if we include it.
            for identifier in party.get('identifiers', []):
                identifier.pop('id', None)
            all_parties.append(party)
        all_parties.sort(key=lambda p: p['id'])
        # Output to a string so that we can strip any trainling whitespace.
        output = json.dumps(all_parties, sort_keys=True, indent=4)
        output = re.sub(r'(?ms)\s*$', '', output)
        ntf.write(output)
        rename(ntf.name, output_filename)
