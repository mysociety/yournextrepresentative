# Take the scraped PPC data and try to import it into PopIt.
#
# It looks for someone with the same name by searching PopIt, and, if
# matches are found, asks the user whether they're the same person.
# This decision is recorded in a JSON file so you should only need to
# make that choice once.
#
# TODO: add a --noinput option, which won't ask for input, but instead
# output text and return an error; this will be useful for running
# this job from cron - if you get an email from cron, you'll need to
# run the script manually to make those decisions.

import os
from os.path import join
import re
import json

from django.core.management.base import BaseCommand
from django.conf import settings

import requests

from candidates.update import PersonParseMixin, PersonUpdateMixin
from candidates.static_data import MapItData
from candidates.views import CandidacyMixin

party_slug_to_popit_party = {
    'labour': {
        'name': 'Labour Party',
        'id': 'party:53',
    },
    'conservatives': {
        'name': 'Conservative Party',
        'id': 'party:52',
    },
    'libdem': {
        'name': 'Liberal Democrats',
        'id': 'party:90',
    }
}

constituency_corrections = {
    'Berwick': 'Berwick-upon-Tweed',
    'Chester': 'City of Chester',
    'Dover and Deal': 'Dover',
    'Hull North': 'Kingston upon Hull North',
    'Hull West and Hessle': 'Kingston upon Hull West and Hessle',
    'Isle of Wright': 'Isle of Wight',
    'Richmond': 'Richmond (Yorks)',
    'Stratford-upon-Avon': 'Stratford-on-Avon',
    'West Cornwall and Scilly': 'St Ives',
}

def cons_key(s):
    return re.sub(r',', '', s).lower()

constituency_lookup = {
    cons_key(k): v for k, v in
    MapItData.constituencies_2010_name_map.items()
}

def get_constituency_from_name(constituency_name):
    name = re.sub(r'\xA0', ' ', constituency_name)
    name = re.sub(r' & ', ' and ', name)
    name = constituency_corrections.get(name, name)
    name = re.sub(r'(?i)candidate for ', '', name)
    mapit_data = constituency_lookup[cons_key(name)]
    post_id = str(mapit_data['id'])
    return {
        'post_id': post_id,
        'name': mapit_data['name'],
        'mapit_url': 'http://mapit.mysociety.org/area/{0}'.format(post_id),
    }

ppc_data_directory = join(
    settings.BASE_DIR,
    'data',
    'UK-Political-Parties',
    'ppcs',
    'json'
)

human_decisions_filename = join(
    settings.BASE_DIR,
    'data',
    'human-ppc-decisions.json'
)

def get_human_decisions():
    with open(human_decisions_filename) as f:
        return json.load(f)

def write_human_decisions(human_decisions):
    output = json.dumps(human_decisions, indent=4, sort_keys=True)
    output = re.sub(r'(?ms)\s*$', '', output)
    with open(human_decisions_filename, 'w') as f:
        f.write(output)

def record_human_decision(ppc_dict, popit_person, same):
    human_decisions = get_human_decisions()
    human_decisions.append({
        'same_person': same,
        'ppc': ppc_dict,
        'popit_person': popit_person,
    })
    write_human_decisions(human_decisions)

def get_human_decision(ppc_data):
    fields_to_match = ['party_slug', 'constituency', 'name']
    matching_decisions = []
    for decision in get_human_decisions():
        if all(decision['ppc'][k] == ppc_data[k] for k in fields_to_match):
            matching_decisions.append(decision)
    return matching_decisions

def merge_person_data(old_data, new_data):
    data = old_data.copy()
    standing_in = data.get('standing_in', {})
    party_memberships = data.get('party_memberships', {})
    standing_in.update(new_data.get('standing_in', {}))
    party_memberships.update(new_data.get('party_memberships', {}))
    data.update(new_data)
    data['standing_in'] = standing_in
    data['party_memberships'] = party_memberships
    return data

def get_ppc_url_from_popit_result(popit_result):
    links = popit_result.get('links', [])
    for link in links:
        if link.get('note') == 'party PPC page':
            return link.get['url']
    return None

class Command(CandidacyMixin, PersonParseMixin, PersonUpdateMixin, BaseCommand):
    help = "Import scraped PPC data"

    # Currently unused:
    #
    #     "region",
    #     "full_url",
    #     "path",
    #     "phone",
    #     "slug",
    #     "address",
    #     "current_mp",
    #     "blog_url",
    #     "campaign_url",
    #     "biography_url",

    def get_person_data_from_ppc(self, ppc_data):
        return {
            'name': ppc_data.get('name', ''),
            'email': ppc_data.get('email', ''),
            'date_of_birth': None,
            'twitter_username': ppc_data.get('twitter_username', ''),
            'facebook_personal_url': ppc_data.get('facebook_url', ''),
            'homepage_url': ppc_data.get('homepage_url', ''),
            'party_ppc_page_url': ppc_data.get('full_url', ''),
            'standing_in': {
                '2015': ppc_data['constituency_object'],
            },
            'party_memberships': {
                '2015': ppc_data['party_object'],
            }
        }

    def update_popit_person(self, popit_person_id, ppc_data):
        # Get the existing data first:
        person_data = self.get_person(popit_person_id)
        previous_versions = person_data.pop('versions')
        new_person_data = self.get_person_data_from_ppc(ppc_data)
        # Remove any empty keys, we don't want to overwrite exiting
        # data with nothing:
        keys = new_person_data.keys()
        for key in keys:
            if not new_person_data[key]:
                del new_person_data[key]
        merged_person_data = merge_person_data(person_data, new_person_data)
        change_metadata = self.get_change_metadata(
            None,
            'Updated candidate from official PPC data ({0})'.format(ppc_data['party_slug']),
        )
        return self.update_person(
            merged_person_data,
            change_metadata,
            previous_versions,
        )

    def add_popit_person(self, ppc_data):
        change_metadata = self.get_change_metadata(
            None,
            'Created new candidate from official PPC data ({0})'.format(ppc_data['party_slug']),
        )
        person_data = self.get_person_data_from_ppc(ppc_data)
        return self.create_person(person_data, change_metadata)

    def already_added_for_2015(self, ppc_data, popit_result):
        popit_constituency_name_2015 = popit_result['standing_in'].get('2015', {}).get('name')
        popit_party_id_2015 = popit_result['party_memberships'].get('2015', {}).get('id')
        return (ppc_data['name'] == popit_result['name'] and
                ppc_data['party_object']['id'] == popit_party_id_2015 and
                ppc_data['constituency_object']['name'] == popit_constituency_name_2015)

    def match_based_on_2010(self, decision_popit, popit_result):
        # We assume that the name is already a match (or a close
        # match) because this came from a search result...
        dsi2010 = decision_popit['standing_in']
        psi2010 = popit_result['standing_in']
        dpm2010 = decision_popit['party_memberships']
        ppm2010 = popit_result['party_memberships']
        for d in (dsi2010, psi2010, dpm2010, ppm2010):
            if '2010' not in d:
                return False
        return (
            dsi2010['2010']['name'] == psi2010['2010']['name'] and
            dpm2010['2010']['name'] == ppm2010['2010']['name']
        )

    def already_matched_to_2010_person(self, ppc_data, popit_result):
        decisions = get_human_decision(ppc_data)
        for decision in decisions:
            popit_person = decision['popit_person']
            if self.match_based_on_2010(popit_person, popit_result):
                return decision['same_person']
        return None

    def decision_from_user(self, ppc_data, popit_result):
        # Ask whether the PPC is the same as this person from the
        # PopIt search results:
        print "--------------------------------------------------------"
        print "Is this PPC ..."
        print "        Name:", ppc_data['name'].encode('utf-8')
        if 'email' in ppc_data:
            print "        Email:", ppc_data['email']
        print "        Party:", ppc_data['party_slug']
        print "        Constituency:", ppc_data['constituency']
        if 'full_url' in ppc_data:
            print "        PPC URL:", ppc_data['full_url']
        print "... the same as this person from PopIt:"
        print "        PopIt URL:", popit_result['html_url']
        print "        Name:", popit_result['name'].encode('utf-8')
        if 'email' in popit_result:
            print "        Email:", popit_result['email']
        for year in popit_result['party_memberships']:
            print "        Party in {0}: {1}".format(
                year, popit_result['party_memberships'][year]['name']
            )
        for year in popit_result['standing_in']:
            print "        Constituency in {0}: {1}".format(
                year, popit_result['standing_in'][year]['name']
            )
        response = ''
        while response.lower() not in ('y', 'n'):
            response = raw_input('Are they the same? (y/Y/n/N) ')
            response = response.lower().strip()
            if response == 'y':
                return True
            elif response == 'n':
                return False

    def handle_person(self, ppc_data):
        print u"PPC ({party_slug}): {name}".format(**ppc_data).encode('utf-8')
        # Search PopIt for anyone with the same name. (FIXME: we
        # should make this a bit fuzzier when the PopIt API
        # supports that.)
        person_search_url = self.get_search_url(
            'persons', '"' + ppc_data['name'] + '"'
        )
        r = requests.get(
            person_search_url
        )
        for result in r.json()['result']:
            # FIXME: With the current code, updating Elasticsearch
            # fails because it rejects the empty string as a null date
            # value. To just get this working, GET the person directly
            # so the information's defintely up to date.
            result = self.api.persons(result['id']).get()['result']
            # We don't need past versions of the person or their
            # memberships, and it's unnecessary verbose to record them
            # with decisions.
            del result['versions']
            del result['memberships']
            if self.already_added_for_2015(ppc_data, result):
                # Then just update that person with the possibly
                # updated scraped data:
                self.update_popit_person(result['id'], ppc_data)
                return
            # Do we already have a decision about whether this PPC is
            # the same as another from 2010?
            decision = self.already_matched_to_2010_person(ppc_data, result)
            if decision is not None:
                if decision:
                    self.update_popit_person(result['id'], ppc_data)
                    return
            else:
                # We have to ask the user for a decision:
                if self.decision_from_user(ppc_data, result):
                    self.update_popit_person(result['id'], ppc_data)
                    record_human_decision(ppc_data, result, True)
                    return
                else:
                    record_human_decision(ppc_data, result, False)
        # If we haven't returned from the function by this stage, we
        # need to create a new candidate in PopIt:
        self.add_popit_person(ppc_data)

    def handle(self, **options):

        for party_slug in sorted(os.listdir(ppc_data_directory)):
            json_directory = join(
                ppc_data_directory,
                party_slug
            )
            for leafname in sorted(os.listdir(json_directory)):
                filename = join(json_directory, leafname)
                with open(filename) as f:
                    ppc_data = json.load(f)
                    ppc_data['party_slug'] = party_slug
                    ppc_data['party_object'] = party_slug_to_popit_party[party_slug]
                    ppc_data['constituency_object'] = get_constituency_from_name(
                        ppc_data['constituency']
                    )
                    self.handle_person(ppc_data)
