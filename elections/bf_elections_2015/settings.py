# -*- coding: utf-8 -*-

from datetime import date

MAPIT_BASE_URL = 'http://international.mapit.mysociety.org/'
ELECTION_RE = '(?P<election>prv-2015|pres-2015|nat-2015)'

AREAS_TO_ALWAYS_RETURN = [
    {
        'area_type_code': 'NATIONAL',
        'area_id': 0,
    }
]

EXTRA_SIMPLE_FIELDS = {
    'cv': '',
    'program': ''
}

SITE_OWNER = 'Burkina Open Data Initiative (BODI)'
COPYRIGHT_HOLDER = 'Burkina Open Data Initiative (BODI)'
