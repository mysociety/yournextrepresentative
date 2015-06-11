from collections import defaultdict
import json
from os.path import abspath, dirname, join, exists

import requests

from django.conf import settings

from candidates.election_specific import area_to_post_group

data_directory = abspath(join(
    dirname(__file__), '..', 'elections', settings.ELECTION_APP, 'data'
))

ALL_MAPIT_TYPES_AND_GENERATIONS = set(
    (mapit_type, t[1]['mapit_generation'])
    for t in settings.ELECTIONS_BY_DATE
    for mapit_type in t[1]['mapit_types']
)

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

# What do we need to do with MapIt data?
#
#  Just area related:
#
#    Go from MapIt ID to full area data (currently areas_by_id, was constituencies_2010)
#    Go from an area name and type to full area data (currently areas_by_name, was constituencies_2010_name_map)
#    Get a list of all areas of a particular type (areas_list_sorted_by_name, was constituencies_2010_name_sorted)
#    Get a list of all areas of a particular type in a given "post group" (currently area_ids_and_names_by_post_group, was constituencies_2010_by_post_group)
#
#  Related to posts too:
#
#    Go from a MapIt ID to the posts are associated with it:
#       (probably need a new class method for that...)

class MapItData(object):

    areas_by_id = {}
    areas_by_name = {}
    areas_list_sorted_by_name = {}
    area_ids_and_names_by_post_group = {}

    for t in ALL_MAPIT_TYPES_AND_GENERATIONS:
        areas_by_id[t] = get_mapit_areas(t[0], t[1])
        for area in areas_by_id[t].values():
            areas_by_name.setdefault(t, {})
            areas_by_name[t][area['name']] = area
        areas_list_sorted_by_name[t] = sorted(
            areas_by_id[t].items(),
            key=lambda c: c[1]['name']
        )
        for area in areas_by_name[t].values():
            post_group = area_to_post_group(area)
            area_ids_and_names_by_post_group.setdefault(t, defaultdict(list))
            area_ids_and_names_by_post_group[t][post_group].append(
                (str(area['id']), area['name'])
            )
        for area_list in area_ids_and_names_by_post_group[t].values():
            area_list.sort(key=lambda c: c[1])

def get_all_parties():
    result_list = defaultdict(list)
    result_dict = {}
    with open(join(data_directory, 'all-parties-from-popit.json')) as f:
        for party in json.load(f):
            key = party.get('register', '')
            result_list[key].append((party['id'], party['name']))
            result_dict[party['id']] = party['name']
        # The parties without a register (e.g. the pseudo parties
        # "Independent" and "Speaker seeking re-election") don't have
        # a register, but should be added to both the Great Britain
        # and Northern Ireland lists:
        for register in ('Great Britain', 'Northern Ireland'):
            result_list[register] += result_list['']
        # Then remove those parties without a register:
        result_list.pop('', None)
        # Now sort the parties, and an an empty default at the start:
        for parties in result_list.values():
            parties.sort(key=lambda p: p[1].lower())
            parties.insert(0, ('party:none', ''))
    return result_list, result_dict

class PartyData(object):
    party_choices, party_id_to_name = get_all_parties()
    party_sets = (
        {'slug': 'gb', 'name': 'Great Britain'},
        {'slug': 'ni', 'name': 'Northern Ireland'},
    )
