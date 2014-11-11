#!/usr/bin/env python

import json
from os.path import dirname, join, realpath

repo_root = realpath(join(dirname(__file__), '..',))

input_filename = join(repo_root, 'data', 'mapit-WMC-generation-22.json')
output_filename = join(repo_root, 'candidates', 'static', 'js', 'mapit-areas-ni.js')

with open(input_filename) as input_file:
    with open(output_filename, 'w') as output_file:
        output_file.write('var isNorthernIreland = ')
        json.dump(
            {
                area_id: True for
                area_id, data in json.load(input_file).items()
                if data['country_name'] == 'Northern Ireland'
            },
            output_file
        )
        output_file.write(';\n')
