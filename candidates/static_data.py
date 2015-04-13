from collections import defaultdict
import json
from os.path import abspath, dirname, join

data_directory = abspath(join(dirname(__file__), '..', 'data'))

def get_mapit_constituencies(basename):
    with open(join(data_directory, basename)) as f:
        return json.load(f)

def get_constituency_name_map(basename):
    result = {}
    for constituency in get_mapit_constituencies(basename).values():
        result[constituency['name']] = constituency
    return result

def get_constituencies_by_country(basename):
    result = defaultdict(list)
    for cons in get_mapit_constituencies(basename).values():
        result[cons['country_name']].append((str(cons['id']), cons['name']))
    for cons_list in result.values():
        cons_list.sort(key=lambda c: c[1])
    return result

class MapItData(object):
    constituencies_2010 = \
        get_mapit_constituencies('mapit-WMC-generation-13.json')
    constituencies_2010_name_map = \
        get_constituency_name_map('mapit-WMC-generation-13.json')
    constituencies_2010_name_sorted = \
        sorted(
            constituencies_2010.items(),
            key=lambda t: t[1]['name']
        )
    constituencies_2010_by_country = \
        get_constituencies_by_country('mapit-WMC-generation-13.json')

def get_descriptions_choices(party):
    result = []
    descriptions = party.get('descriptions', [])
    for d in descriptions:
        print "d is:", d
        versions = [d[k] for k in ('description', 'translation') if d[k]]
        print "versions is:", versions
        result.append(u" / ".join(versions))
    return result

def get_all_parties():
    all_descriptions_choices = []
    party_id_to_description_choices ={}
    result_list = defaultdict(list)
    result_dict = {}
    with open(join(data_directory, 'all-parties-from-popit.json')) as f:
        for party in json.load(f):
            key = party.get('register', '')
            result_list[key].append((party['id'], party['name']))
            result_dict[party['id']] = party['name']
            description_choices = get_descriptions_choices(party)
            all_descriptions_choices += description_choices
            party_id_to_description_choices[party['id']] = \
                description_choices
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
    for description in all_descriptions_choices:
        print description
    return result_list, result_dict, all_descriptions_choices, party_id_to_description_choices

class PartyData(object):
    party_choices, party_id_to_name, all_descriptions_choices, party_id_to_description_choices = \
        get_all_parties()
