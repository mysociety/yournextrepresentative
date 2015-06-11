from datetime import date

ELECTIONS = {
    '2010': {
        'for_post_role': 'Member of Parliament',
        'election_date': date(2010, 5, 6),
        'candidacy_start_date': date(2005, 5, 6),
        'organization_id': 'commons',
        'name': '2010 General Election',
        'current': False,
        'use_for_candidate_suggestions': True,
        'party_membership_start_date': date(2005, 5, 6),
        'party_membership_end_date': date(2010, 5, 6),
        'mapit_types': ['WMC'],
        'mapit_generation': 22,
        'get_post_id': lambda mapit_type, area_id: str(area_id),
    },
    '2015': {
        'for_post_role': 'Member of Parliament',
        'election_date': date(2015, 5, 7),
        'candidacy_start_date': date(2010, 5, 7),
        'organization_id': 'commons',
        'name': '2015 General Election',
        'current': True,
        'party_membership_start_date': date(2010, 5, 7),
        'party_membership_end_date': date(9999, 12, 31),
        'mapit_types': ['WMC'],
        'mapit_generation': 22,
        'get_post_id': lambda mapit_type, area_id: str(area_id),
    }
}

MAPIT_BASE_URL = 'http://mapit.mysociety.org/'
