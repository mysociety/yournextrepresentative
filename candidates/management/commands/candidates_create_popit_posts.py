from collections import defaultdict

from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.translation import ugettext as _

from candidates.models.popit import create_or_update
from candidates.popit import PopItApiMixin
from candidates.election_specific import AREA_DATA, AREA_POST_DATA

from elections.models import Election

from slumber.exceptions import HttpServerError, HttpClientError


class NoValuesError(Exception):
    pass


class NonUniqueValuesError(Exception):
    pass


def all_posts_in_all_elections():
    """A generator function to yield data on every post for every election

    The purpose of this generator function is to iterate over every
    post that should exist and yield the post ID along with the
    election and area data it should be associated with.

    It might not be obvious that posts can appear in multiple
    elections; this means that you might get the same post ID yielded
    more than once, but with different election and area data."""

    for election_data in Election.objects.all():
        for mapit_type in election_data.area_types.all():
            mapit_tuple = (mapit_type.name, election_data.area_generation)
            for area_id, area in AREA_DATA.areas_by_id[mapit_tuple].items():
                post_id = AREA_POST_DATA.get_post_id(
                    election_data.slug, mapit_type, area_id
                )
                yield {
                    'election': election_data.slug,
                    'election_data': election_data,
                    'mapit_type': mapit_type,
                    'area_id': area_id,
                    'area': area,
                    'post_id': post_id,
                }


def get_unique_value(seq):
    """Make sure a sequence has only a single unique value and return that

    If there are actually 0 or more than 1 distinct values in the
    sequence, raise a NoValuesError or NonUniqueValuesError"""

    unique_values = set(sorted(seq))
    if not unique_values:
        raise NoValuesError('No values in the sequence')
    if len(unique_values) > 1:
        msg = 'Non-unique values found: {0}'
        raise NonUniqueValuesError(msg.format(seq))
    return next(iter(unique_values))


class Command(PopItApiMixin, BaseCommand):
    help = "Create or update the required posts in PopIt"

    option_list = BaseCommand.option_list + (
        make_option(
            '--post-label',
            help='Override the format string used to construct the post label [default: "%default"]',
            default=_('{post_role} for {area_name}'),
        ),
    )

    def handle(self, **options):
        # Choose an appropriate format for the post labels:
        post_label_format = _('{post_role} for {area_name}')
        if options['post_label']:
            post_label_format = options['post_label']
        # Find all the source data for each post:
        post_id_to_all_data = defaultdict(list)
        for data in all_posts_in_all_elections():
            post_id_to_all_data[data['post_id']].append(data)
        # Now we have a mapping from each post to all the data
        # (e.g. elections, areas) it's associated with.  Now try to
        # reconcile that data and create or update the posts:
        try:
            for post_id, data_list in post_id_to_all_data.items():

                # Since the post's creation can be required by multiple
                # elections with different metadata, there might be
                # contradictory values for the properties we want to set
                # on the post. To detect this possibility, we use
                # get_unique_value to extract these values:
                role = get_unique_value(
                    d['election_data'].for_post_role for d in data_list
                )
                organization_id = get_unique_value(
                    d['election_data'].organization_id for d in data_list
                )
                area_id = get_unique_value(d['area_id'] for d in data_list)

                # We can have, however, have multiple values in the
                # 'elections' attribute, so it's fine to collect all of them:
                elections = sorted(set(d['election'] for d in data_list))

                # At this stage we know there's a unique area (since
                # otherwise there wouldn't be a unique area_id) so we
                # don't need to check the uniqueness of area, or the
                # values derived from area.
                area = data_list[0]['area']
                area_mapit_url = \
                    settings.MAPIT_BASE_URL + 'area/' + str(area['id'])
                label = post_label_format.format(
                    post_role=role, area_name=area['name']
                )

                post_data = {
                    'elections': elections,
                    'role': role,
                    'id': post_id,
                    'label': label,
                    'area': {
                        'name': area['name'],
                        'id': 'mapit:' + str(area_id),
                        'identifier': area_mapit_url,
                    },
                    'organization_id': organization_id,
                }

                create_or_update(self.api.posts, post_data)

        except (HttpServerError, HttpClientError) as hse:
            print "The body of the error was:", hse.content
            raise
