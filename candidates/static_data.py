from collections import defaultdict
import json
from os.path import abspath, dirname, join, exists
import sys

import requests

from django.conf import settings
from django.utils.translation import ugettext as _

from popolo.models import Organization
from elections.models import Election

data_directory = abspath(join(
    dirname(__file__), '..', 'elections', settings.ELECTION_APP, 'data'
))

def get_mapit_areas(area_type, generation):
    expected_filename = join(
        data_directory,
        'mapit-{area_type}-generation-{generation}.json'.format(
            area_type=area_type,
            generation=generation,
        )
    )
    if exists(expected_filename):
        with open(expected_filename) as f:
            return json.load(f)
    else:
        mapit_url_format = '{base_url}areas/{area_type}?generation={generation}'
        mapit_url = mapit_url_format.format(
            base_url=settings.MAPIT_BASE_URL,
            area_type=area_type,
            generation=generation
        )
        message = "WARNING: failed to find {filename} so loading from MapIt\n"
        message += "This will make start-up slow and less reliable, so consider\n"
        message += "committing a copy of: {url}"
        print message.format(filename=expected_filename, url=mapit_url)
        r = requests.get(mapit_url)
        return r.json()


class BaseMapItData(object):

    """Load MapIt data and make it availale in helpful data structures

    FIXME: check that these are sensible descriptions

    On instantiation, the following attributes are created:

        'areas_by_id', a dictionary that maps from a MapIt ID to full
        area data

        'areas_by_name', a dictionary that maps an area name and typ
        to full area data

        'areas_list_sorted_by_name', a list of all areas of a
        particular type

    """

    def __init__(self):

        self.areas_by_id = {}
        self.areas_by_name = {}
        self.areas_list_sorted_by_name = {}

        for t, election_tuples in Election.objects.elections_for_area_generations().items():
            mapit_type, mapit_generation = t
            self.areas_by_id[t] = get_mapit_areas(mapit_type, mapit_generation)
            for area in self.areas_by_id[t].values():
                self.areas_by_name.setdefault(t, {})
                self.areas_by_name[t][area['name']] = area
            self.areas_list_sorted_by_name[t] = sorted(
                self.areas_by_id[t].items(),
                key=lambda c: c[1]['name']
            )


class BaseAreaPostData(object):

    """Instantiate this class to provide mappings between areas and posts

    FIXME: check that these are sensible descriptions

    If you instantiate this class you will get the following attributes:

         'area_ids_and_names_by_post_group', maps a post group to a
         list of all areas of a particular type

         'areas_by_post_id', maps a post ID to all areas associated
         with it
    """

    def area_to_post_group(self, area_data):
        raise NotImplementedError(
            "You should implement area_to_post_group in a subclass"
        )

    def get_post_id(self, election, area_type, area_id):
        return Election.objects.get_by_slug(election).post_id_format.format(
            area_id=area_id
        )

    def __init__(self, area_data):
        self.area_data = area_data
        self.areas_by_post_id = {}
        self.area_ids_and_names_by_post_group = {}

        for area_tuple, election_tuples in Election.objects.elections_for_area_generations().items():
            for election_data in election_tuples:
                area_type, area_generation = area_tuple
                for area in self.area_data.areas_by_id[area_tuple].values():
                    post_id = self.get_post_id(election_data.slug, area_type, area['id'])
                    if post_id in self.areas_by_post_id:
                        message = _("Found multiple areas for the post ID {post_id}")
                        raise Exception(message.format(post_id=post_id))
                    self.areas_by_post_id[post_id] = area
                for area in area_data.areas_by_name[area_tuple].values():
                    post_group = self.area_to_post_group(area)
                    self.area_ids_and_names_by_post_group.setdefault(area_tuple, defaultdict(list))
                    self.area_ids_and_names_by_post_group[area_tuple][post_group].append(
                        (str(area['id']), area['name'])
                    )
                for area_list in self.area_ids_and_names_by_post_group[area_tuple].values():
                    area_list.sort(key=lambda c: c[1])
