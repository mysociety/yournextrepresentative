from collections import defaultdict
import json
from os.path import abspath, dirname, join
import sys

from .popit import create_popit_api_object, popit_unwrap_pagination

data_directory = abspath(join(dirname(__file__), '..', 'data'))

print >> sys.stderr, "Loading MapIt data..."

def get_mapit_constituencies(basename):
    with open(join(data_directory, basename)) as f:
        return json.load(f)

def get_constituency_name_map(basename):
    result = {}
    for constituency in get_mapit_constituencies(basename).values():
        result[constituency['name']] = constituency
    return result

class MapItData(object):
    constituencies_2010 = \
        get_mapit_constituencies('mapit-WMC-generation-13.json')
    constituencies_2010_name_map = \
        get_constituency_name_map('mapit-WMC-generation-13.json')

print >> sys.stderr, "Loading party data from PopIt..."

def get_all_parties():
    result_list, result_dict = defaultdict(list), {}
    api = create_popit_api_object()
    for party in popit_unwrap_pagination(api.organizations, embed=''):
        if party['classification'] != 'Party':
            continue
        key = party.get('register', '')
        result_list[key].append((party['id'], party['name']))
        result_dict[party['id']] = party['name']
    for parties in result_list.values():
        parties.sort(key=lambda p: p[1].lower())
        parties.insert(0, ('party:none', ''))
    return result_list, result_dict

class PartyData(object):
    party_choices, party_id_to_name = get_all_parties()
