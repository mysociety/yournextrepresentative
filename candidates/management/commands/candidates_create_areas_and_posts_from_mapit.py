from __future__ import unicode_literals

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from django.utils.translation import ugettext as _
from django.utils.six.moves.urllib_parse import urljoin, urlsplit
from django.utils.six import text_type

import requests

from popolo.models import Post, Area
from candidates.models import PostExtra, AreaExtra, PartySet, PostExtraElection
from elections.models import Election, AreaType


"""
This assumes that all the elections in the instance are the same as
far as posts and organization are concerned. It will not work for
instances with different types of election - e.g. Presidential and
parliamentary.
"""
class Command(BaseCommand):
    help = """Create areas and posts based on a mapit area type

MAPIT-URL should be something that returns a set of JSON results
containing areas of type AREA_TYPE. An Area and Post will be created
for each area found using the post and organization information
in the Election objects in the app.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            'MAPIT-URL',
            help='The base URL of the MapIt instance, e.g. ' \
                'http://global.mapit.mysociety.org/'
        )
        parser.add_argument(
            'AREA-TYPE',
            help='The code of the MapIt area type, e.g. WMC'
        )
        parser.add_argument(
            'POST-ID-FORMAT',
            help='The format of the corresponding Post ID, e.g. cons-{area_id}'
        )
        parser.add_argument(
            '--area-ids',
            help='Manually specify the MapIt area IDs to create posts for',
            metavar='AREA-IDS',
        )
        parser.add_argument(
            '--post-label',
            help='Override the format string used to construct the post label [default: "%(default)s"]',
            metavar='POST-LABEL',
            default=_('{post_role} for {area_name}'),
        )
        parser.add_argument(
            '--party-set',
            help='Use a particular party set for all the posts [default: "%(default)s"]',
            metavar='PARTY-SET-NAME',
            default='National',
        )
        parser.add_argument(
            '--enclosing-area-id',
            help='Only find areas covered by the area with this ID',
            metavar='AREA-ID',
            type=int
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            self.handle_inner(*args, **options)

    def handle_inner(self, *args, **options):
        post_label_format = options['post_label']

        mapit_url = options['MAPIT-URL']
        split_mapit_url = urlsplit(mapit_url)
        if any([split_mapit_url.path not in ('', '/'),
                split_mapit_url.query,
                split_mapit_url.fragment]):
            raise CommandError("MAPIT-URL must only be the base URL, "
                "with no path, query or fragment")
        area_type = options['AREA-TYPE']
        post_id_format = options['POST-ID-FORMAT']
        manual_area_ids = []
        if options['area_ids']:
            try:
                manual_area_ids = [
                    int(n, 10) for n in options['area_ids'].split(',')
                ]
            except ValueError:
                raise Command("The --area-ids option must be comma separated numeric IDs")
        enclosing_area_id = options['enclosing_area_id']
        if enclosing_area_id:
            # Just check that area actually exists:
            enclosing_area_url = urljoin(
                mapit_url,
                '/area/{0}'.format(enclosing_area_id))
            r = requests.get(enclosing_area_url)
            if r.status_code == 404:
                msg = "The enclosing area {0} doesn't exist"
                raise CommandError(msg.format(enclosing_area_url))

        party_set, created = PartySet.objects.get_or_create(
            slug=slugify(options['party_set']),
            defaults={'name': options['party_set']}
        )

        elections = Election.objects.all()

        if elections.count() == 0:
            raise CommandError("There must be at least one election")

        for election in elections:
            if manual_area_ids:
                all_areas_url = urljoin(mapit_url, '/areas/' + ','.join(
                    text_type(a_id) for a_id in manual_area_ids
                ))
            else:
                query = {}
                if enclosing_area_id:
                    all_areas_url = enclosing_area_url + '/covers?type=' + area_type
                    query['type'] = area_type
                else:
                    all_areas_url = urljoin(mapit_url, '/areas/{0}'.format(area_type))
                if election.area_generation:
                    query['generation'] = election.area_generation
                query_string = '&'.join('{0}={1}'.format(k, v) for k, v in query.items())
                if query_string:
                    all_areas_url += '?' + query_string

            mapit_result = requests.get(all_areas_url)
            mapit_json = mapit_result.json()

            if 'error' in mapit_json:
                raise Command("Fetching the areas failed: {0}".format(
                    mapit_json['error']))

            for_post_role = election.for_post_role
            org = election.organization

            if org is None:
                raise CommandError("Election {0} requires an organization".format(election.slug))

            for item in mapit_json.items():
                area_json = item[1]

                area_url = urljoin(mapit_url, '/area/' + text_type(area_json['id']))

                area, area_created = Area.objects.get_or_create(
                    name=area_json['name'],
                    identifier=area_url,
                    classification=area_json['type_name']
                )

                area_type, created = AreaType.objects.get_or_create(
                    name=area_json['type'],
                    source='MapIt'
                )

                if area_created:
                    area_extra, area_extra_created = AreaExtra.objects.get_or_create(
                        base=area
                    )

                if area_created and area_extra_created:
                    area_extra.type = area_type
                    area_extra.save()

                post_id = post_id_format.format(area_id=area_json['id'])
                post_name = post_label_format.format(
                    area_name=area_json['name'],
                    post_role=for_post_role
                )

                post, created = Post.objects.get_or_create(
                    label=post_name,
                    area=area,
                    organization=org
                )

                post_extra, created = PostExtra.objects.get_or_create(
                    base=post,
                    slug=post_id,
                    defaults={'party_set': party_set},
                )

                PostExtraElection.objects.get_or_create(
                    postextra=post_extra,
                    election=election,
                )
