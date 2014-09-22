#!/usr/bin/env python

from collections import defaultdict
from datetime import date, timedelta
import json
from optparse import OptionParser
import os
from os.path import join, dirname, realpath
from random import randint
import re
import requests
import slumber
import sys
import time

from popit_api import PopIt
from slugify import slugify
import yaml

directory = realpath(os.path.dirname(__file__))
configuration_file = join(directory, 'conf', 'general.yml')
with open(configuration_file) as f:
    conf = yaml.load(f)

parser = OptionParser()
parser.add_option("--create", action="store_true", default=False,
                  help="Create the example person and organization")
parser.add_option("--delete", action="store_true", default=False,
                  help="Delete the example person and organization")

options, args = parser.parse_args()

try:

    api_properties = {
        'instance': conf['POPIT_INSTANCE'],
        'hostname': conf['POPIT_HOSTNAME'],
        'port': conf.get('POPIT_PORT', 80),
        'api_version': 'v0.1',
    }

    popit_api_key = conf.get('POPIT_API_KEY')
    popit_user = conf.get('POPIT_USER')
    popit_password = conf.get('POPIT_PASSWORD')

    if popit_api_key:
        api_properties['api_key'] = popit_api_key
    else:
        api_properties['user'] = popit_user
        api_properties['password'] = popit_password

    api = PopIt(**api_properties)

    person_id = 'joe-example-bloggs'
    organization_id = 'example-institute'

    if options.create:

        print "Creating person:", person_id
        api.persons.post({
            'id': person_id,
            'name': 'Joe Example Bloggs',
        })

        print "Creating organization:", organization_id
        api.organizations.post({
            'id': organization_id,
            'name': 'institute-of-examples',
        })

        print "Creating membership:", person_id, "member of", organization_id
        api.memberships.post({
            'person_id': person_id,
            'organization_id': organization_id
        })

    if options.delete:
        person = api.persons(person_id).get()
        for m in person['result']['memberships']:
            print "Deleting membership:", m['person_id'], "member of", m['organization_id']
            api.memberships(m['id']).delete()
        print "Deleting organization:", organization_id
        api.organizations(organization_id).delete()
        print "Deleting person:", person_id
        api.persons(person_id).delete()
        sys.exit(0)

    print "Getting person data with GET:"
    person_data = api.persons(person_id).get()
    print "The number of memberships is:", len(person_data['result'].get('memberships', []))

    print "Now updating the person with PUT:"
    date_of_birth = "1970-04-" + str(randint(1, 30))
    api.persons(person_id).put({
        'id': person_id,
        'name': 'Joe Example Bloggs',
        'date_of_birth': date_of_birth
    })

    print "Now re-getting person data with GET:"
    person_data = api.persons(person_id).get()
    print "The number of memberships is:", len(person_data['result'].get('memberships', []))

    time.sleep(5)
    print "Now re-getting person data yet again with GET:"
    person_data = api.persons(person_id).get()
    print "The number of memberships is:", len(person_data['result'].get('memberships', []))


except Exception as e:
    print "Got exception:", e
    if hasattr(e, 'content'):
        print "The exception body content was:", e.content
    raise
