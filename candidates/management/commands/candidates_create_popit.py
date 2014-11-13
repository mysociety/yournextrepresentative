#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import date, timedelta
import json
import os
import re
import requests

from popit_api import PopIt
from slugify import slugify
from slumber.exceptions import HttpServerError

from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError

from candidates.models import (
    MaxPopItIds, election_date_2005, election_date_2010
)
from candidates.popit import popit_unwrap_pagination

ec_registers = ('Great Britain', 'Northern Ireland')

def normalize_party_name(party_name):
    '''Remove any capitalized definite article, non-letter, and downcase'''
    result = re.sub(r'\bThe\b\s*', '', party_name)
    result = re.sub(r'\W', '', result)
    return result.lower()

def organization_active(org, when_date):
    '''Return whether an organization dict was active on when_date'''
    start_date = org.get('founding_date', '0000-01-01')
    end_date = org.get('dissolution_date', '9999-12-31')
    return start_date <= when_date <= end_date

def get_all_parties(api, when_date):
    '''Fetch all political parties from PopIt divided into active / inactive'''
    result = {}
    for register in ec_registers:
        result[register] = {
            'active': {},
            'inactive': {},
        }
    for org in popit_unwrap_pagination(api.organizations, embed=''):
        if org['classification'] != 'Party':
            continue
        org_register = org.get('register')
        if org_register not in ec_registers:
            message = u"Unknown register {0} in organization: {1}"
            # raise Exception, message.format(org_register, org)
            print (u"Warning:" + message.format(org_register, org)).encode('utf-8')
            continue
        register_dict = result[org_register]
        party_dict = register_dict[
            'active' if organization_active(org, when_date) else 'inactive'
        ]
        party_dict[normalize_party_name(org['name'])] = org
    return result

party_name_corrections = {
    'English Democrats Party': 'English Democrats',
    'Scottish National Party': 'Scottish National Party (SNP)',
    # Source: http://en.wikipedia.org/wiki/Respect_Party (footnotes
    # mention the "The Unity Coalition" name)
    'Respect - The Unity Coalition': 'The Respect Party',
    # Source: http://en.wikipedia.org/wiki/Animal_Welfare_Party
    'Animals Count': 'Animal Welfare Party',
    # Source:
    # http://alternativese4.com/2014/04/29/five-things-to-watch-out-for-at-mays-council-elections-in-lewisham/
    # mentions the various name changes of this party:
    'Lewisham For People Not Profit': 'Lewisham People Before Profit',
    # Source:
    # http://en.wikipedia.org/wiki/Ulster_Conservatives_and_Unionists
    # says that they were officially registered as
    # "Conservatives and Unionists – New Force (UCUNF)",
    # which is very close one of the Description elements of
    # "Conservative and Unionist Party" (PP 51) on the
    # Electoral Commission website: "Ulster Conservatives
    # and Unionists - New Force (Joint Description with
    # Ulster Unionist Party)"
    'Ulster Conservatives and Unionists': 'Conservative and Unionist Party',
}

def find_party_from_name(ec_party_data, ynmp_party_name, register):
    corrected_name = party_name_corrections.get(ynmp_party_name)
    if corrected_name:
        ynmp_party_name = corrected_name
    register_dict = ec_party_data[register]
    key = normalize_party_name(ynmp_party_name)
    active_result = register_dict['active'].get(key)
    inactive_result = register_dict['inactive'].get(key)
    return active_result or inactive_result

def update_or_create(api_collection, object_id, properties):
    # FIXME: should be library code, or in the API!
    try:
        return api_collection.post(properties)
    except HttpServerError as hse:
        error = json.loads(hse.content)
        if error.get('error', {}).get('code') == 11000:
            return api_collection(object_id).put(properties)
        else:
            raise

class Command(NoArgsCommand):
    help = "Import data in to PopIt"
    def handle_noargs(self, **options):
        try:
            self.import_data()
        except Exception as e:
            print "got exception:", e
            if hasattr(e, 'content'):
                print "the exception body was:", e.content
            raise CommandError(e.message)

    def import_data(self):

        api = PopIt(
            instance=settings.POPIT_INSTANCE,
            hostname=settings.POPIT_HOSTNAME,
            port=getattr(settings, 'POPIT_PORT', 80),
            api_version='v0.1',
            api_key=settings.POPIT_API_KEY
           )

        main_json = os.path.join(
            settings.BASE_DIR,
            'data',
            'yournextmp-json_main-20140124-030234.json',
           )

        with open(main_json) as f:
            main_data = json.load(f)

        r = requests.get('http://mapit.mysociety.org/areas/WMC')
        wmc_data = r.json()

        # We want a mapping between Westminster constituency name and seat ID:
        wmc_name_to_seat = {}
        for seat_id, seat in main_data['Seat'].items():
            wmc_name_to_seat[seat['name']] = seat_id

        seat_id_to_wmc = {}
        for wmc in wmc_data.values():
            seat_id_to_wmc[wmc_name_to_seat[wmc['name']]] = wmc

        # Build a mapping between seat ID and candidate IDs:
        seat_id_to_candidacy_id = defaultdict(set)
        for candidacy_id, candidacy in main_data['Candidacy'].items():
            seat_id_to_candidacy_id[candidacy['seat_id']].add(candidacy_id)

        # Possibly not needed:
        commons_id = 'commons'
        api.organizations.post({
            'id': commons_id,
            'name': 'House of Commons',
            'classification': 'UK House of Parliament',
        })

        # Get all Westminster constituencies from MapIt

        r = requests.get('http://mapit.mysociety.org/areas/WMC')
        wmc_data = r.json()

        cons_to_post = {}

        for wmc in wmc_data.values():
            wmc_name = wmc['name']
            post_id = str(wmc['id'])
            api.posts.post({
                'id': post_id,
                'label': 'Member of Parliament for ' + wmc_name,
                'role': 'Member of Parliament',
                'organization_id': commons_id,
                'start_date': str(election_date_2005 + timedelta(days=1)),
                'area': {
                    'id': 'mapit:' + str(wmc['id']),
                    'name': wmc['name'],
                    'identifier': 'http://mapit.mysociety.org/area/' + str(wmc['id'])
                }
            })
            cons_to_post[wmc_name] = post_id

        # We need the party name rather than the YNMP party_id in
        # order to look up the parties in the electoral commission
        # data:

        party_id_to_ynmp_name = {}
        for party_id, party in main_data['Party'].items():
            party_id_to_ynmp_name[party_id] = party['name']

        # Create all the people, and their party memberships:
        candidate_id_to_party_id = {}
        max_id = 0
        for candidate_id, candidate in main_data['Candidate'].items():
            max_id = max(max_id, candidate_id)
            slug = candidate['code'].replace('_', '-')
            properties = {
                'id': candidate_id,
                'slug': slug,
                'name': candidate['name'],
                'identifiers': [
                    {
                        'scheme': 'yournextmp-candidate',
                        'identifier': candidate_id,
                    }
                ],
            }
            dob = candidate['dob']
            if dob:
                m = re.search(r'(\d+)/(\d+)/(\d+)', dob)
                if m:
                    d = date(*reversed([int(x, 10) for x in m.groups()]))
                    properties['birth_date'] = str(d)
            for k in ('gender', 'email', 'phone'):
                properties[k] = candidate[k]
            api.persons.post(properties)
            candidate_id_to_party_id[candidate_id] = candidate['party_id']

        unknown_party_counts = {
            'Great Britain': defaultdict(int),
            'Northern Ireland': defaultdict(int),
        }

        ec_party_data = get_all_parties(api, str(election_date_2010))

        # Go through all the candidacies and create memberships from them:
        for candidacy_id, candidacy in main_data['Candidacy'].items():
            candidate_id = candidacy['candidate_id']
            wmc = seat_id_to_wmc[candidacy['seat_id']]
            if wmc['country_name'] == 'Northern Ireland':
                register = 'Northern Ireland'
            else:
                register = 'Great Britain'
            post = cons_to_post[wmc['name']]
            if main_data['Candidate'][candidacy['candidate_id']]['status'] == 'standing':
                properties = {
                    'person_id': candidate_id,
                    'post_id': post,
                    'role': 'Candidate',
                    'start_date': str(election_date_2005 + timedelta(days=1)),
                    'end_date': str(election_date_2010),
                }
                print "creating candidacy with properties:", json.dumps(properties)
                api.memberships.post(properties)
            # Find the right party given the country that this constituency is in:
            party_id = candidate_id_to_party_id[candidate_id]
            party_name = party_id_to_ynmp_name[party_id]
            party_org = find_party_from_name(
                ec_party_data, party_name, register
            )
            if not party_org:
                unknown_party_counts[register][party_name] += 1
                ynmp_id = 'ynmp-party:{0}'.format(party_id)
                result = update_or_create(
                    api.organizations,
                    ynmp_id,
                    {
                        'id': ynmp_id,
                        'slug': slugify(party_name),
                        'classification': 'Party',
                        'name': party_name,
                        'identifiers': [
                            {
                                'identifier': party_id,
                                'scheme': 'ynmp-party',
                            }
                        ]
                    })
                party_org = result['result']

            # FIXME: remove any other party membership for 2010, in
            # case the party resolution has been corrected prior to
            # this run.
            api.memberships.post({
                'person_id': candidate_id,
                'organization_id': party_org['id'],
            })

        for register in ec_registers:
            print "=== Unknown parties in the", register, "register:"
            party_names_and_counts = unknown_party_counts[register].items()
            party_names_and_counts.sort(key=lambda t: t[1], reverse=True)
            for name, count in party_names_and_counts:
                print count, name

        print "The maximum person ID is %s" % max_id
        MaxPopItIds.update_max_persons_id(max_id)
