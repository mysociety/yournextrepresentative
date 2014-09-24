#!/usr/bin/env python

from collections import defaultdict
from datetime import date, timedelta
import json
import optparse
import os
from os.path import join, dirname, realpath
import re
import requests
import slumber
import sys

from popit_api import PopIt
from slugify import slugify
import yaml

directory = realpath(os.path.dirname(__file__))
configuration_file = join(directory, 'conf', 'general.yml')
with open(configuration_file) as f:
    conf = yaml.load(f)

try:

    api = PopIt(
        instance=conf['POPIT_INSTANCE'],
        hostname=conf['POPIT_HOSTNAME'],
        port=conf.get('POPIT_PORT', 80),
        api_version='v0.1',
        user=conf['POPIT_USER'],
        password=conf['POPIT_PASSWORD'],
       )


    main_json = os.path.join(
        directory,
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

    election_date_2005 = date(2005, 5, 5)
    election_date_2010 = date(2010, 5, 6)

    # Get all Westminster constituencies from MapIt

    r = requests.get('http://mapit.mysociety.org/areas/WMC')
    wmc_data = r.json()

    cons_to_organization_2010 = {}
    cons_to_organization_2015 = {}

    for wmc in wmc_data.values():
        wmc_name = wmc['name']
        wmc_slug = slugify(wmc_name)
        # Say that the candidate lists start on the day after an election,
        # and end on the day of the election.  (Queries that test whether
        # an organisation currently exists should test for a date <= the
        # dissolution date.)
        slug_2010 = 'candidates-2010-' + wmc_slug
        slug_2015 = 'candidates-2015-' + wmc_slug
        api.organizations.post({
            'id': slug_2010,
            'name': 'Candidates for ' + wmc['name'] + ' in 2010',
            'classification': 'Candidate List',
            'founding_date': str(election_date_2005 + timedelta(days=1)),
            'dissolution_date': str(election_date_2010),
        })
        cons_to_organization_2010[wmc_name] = slug_2010
        api.organizations.post({
            'id': slug_2015,
            'name': 'Candidates for ' + wmc['name'] + ' in 2015',
            'classification': 'Candidate List',
            'founding_date': str(election_date_2010 + timedelta(days=1)),
        })
        cons_to_organization_2015[wmc_name] = slug_2015

    # Create all the parties:
    party_id_to_organisation = {}
    for party_id, party in main_data['Party'].items():
        slug = slugify(party['name'])
        # FIXME: add identifiers
        api.organizations.post({
            'id': slug,
            'classification': 'Party',
            'name': party['name']
        })
        party_id_to_organisation[party_id] = slug

    # Create all the people, and their party memberships:
    candidate_id_to_person = {}
    for candidate_id, candidate in main_data['Candidate'].items():
        slug = candidate['code'].replace('_', '-')
        candidate_id_to_person[candidate_id] = slug
        properties = {
            'id': slug,
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
        api.memberships.post({
            'person_id': slug,
            'organization_id': party_id_to_organisation[candidate['party_id']],
        })

    # Go through all the candidacies and create memberships from them:
    for candidacy_id, candidacy in main_data['Candidacy'].items():
        wmc = seat_id_to_wmc[candidacy['seat_id']]
        candidate_list = cons_to_organization_2010[wmc['name']]
        if main_data['Candidate'][candidacy['candidate_id']]['status'] == 'standing':
            properties = {
                'person_id': candidate_id_to_person[candidacy['candidate_id']],
                'organization_id': candidate_list,
                'area': {
                    'id': 'mapit:' + str(wmc['id']),
                    'name': wmc['name'],
                    'identifier': 'http://mapit.mysociety.org/area/' + str(wmc['id'])
                }
            }
            print "creating candidacy with properties:", json.dumps(properties)
            api.memberships.post(properties)
except Exception as e:
    print "got exception:", e
    if hasattr(e, 'content'):
        print "the exception body was:", e.content
    raise
