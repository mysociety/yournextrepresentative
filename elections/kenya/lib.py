from __future__ import unicode_literals

import re

def shorten_post_label(post_label):
    return re.sub(r'^Member of Parliament for ', '', post_label)


def get_local_area_id(area):

    type_to_code_map = {
        'DIS': ['2017_coun', 'county:'],
        'CON': ['2017_cons', 'constituency:'],
        'WRD': ['2017_ward', 'ward:']
    }

    # area[1] is the actual response object
    data = area[1]

    # Country just has a straight ID
    if data['type'] == 'CTR':
        return 'country:' + area[0]

    else:
        return type_to_code_map[data['type']][1] + data['codes'][type_to_code_map[data['type']][0]]
