#!/usr/bin/env python

import csv
import json
import os
from os.path import join, realpath
import requests
import sys
import urlparse
import yaml

directory = realpath(os.path.dirname(__file__))
configuration_file = join(directory, '..', 'conf', 'general.yml')
with open(configuration_file) as f:
    conf = yaml.load(f)

try:

    netloc = '{0}.{1}'.format(conf['POPIT_INSTANCE'], conf['POPIT_HOSTNAME'])
    port = conf.get('POPIT_PORT', 80)
    if str(port) != "80":
        netloc += ":" + str(port)

    url = urlparse.urlunsplit(
        ('http', netloc, '/api/v0.1/organizations', 'per_page=200', '')
    )

    results = []

    while url:
        r = requests.get(url)
        data = r.json()
        for o in data['result']:
            if o.get('classification', '') != 'Party':
                continue
            organization_id = o['id']
            organization_name = o['name'].encode('utf-8')
            candidate_count = len(o.get('memberships', []))
            results.append((organization_id, organization_name, candidate_count))
        url = data.get('next_url')

    with open('parties-2010-rough-candidate-counts.csv', 'wb') as f:
        writer = csv.writer(f)
        for result in sorted(results, key=lambda r: r[2], reverse=True):
            writer.writerow(result)

except Exception as e:
    print "Got exception:", e
    if hasattr(e, 'content'):
        print "The exception body content was:", e.content
    raise
