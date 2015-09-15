# -*- coding: utf-8 -*-

from datetime import date

ELECTIONS = {
    # Party primaries for the chamber of deputies:
    'council-member-2015': {
        'for_post_role': 'Council Member',
        'candidate_membership_role': 'Candidate',
        'winner_membership_role': 'Candidate',
        'election_date': date(2015, 11, 3),
        'candidacy_start_date': date(2015, 6, 22),
        'name': 'Municipal Election',
        'current': True,
        'use_for_candidate_suggestions': False,
        'party_membership_start_date': date(2015, 6, 22),
        'party_membership_end_date': date(9999, 12, 31),
        'mapit_types': ['WARD'],
        'mapit_generation': 1,
        'organization_id': 'saint-paul-city-council',
        'organization_name': 'Saint Paul City Council',
        'post_id_format': 'ward-{area_id}',
    },
    'school-board-2015': {
        'for_post_role': 'School Board Member',
        'candidate_membership_role': 'Candidate',
        'winner_membership_role': 'Candidate',
        'election_date': date(2015, 11, 3),
        'candidacy_start_date': date(2015, 6, 22),
        'name': 'Municipal Election',
        'current': True,
        'use_for_candidate_suggestions': False,
        'party_membership_start_date': date(2015, 6, 22),
        'party_membership_end_date': date(9999, 12, 31),
        'mapit_types': ['MUN'],
        'mapit_generation': 1,
        'organization_id': 'saint-paul-school-board',
        'organization_name': 'Saint Paul School Board',
        'post_id_format': 'city-{area_id}',
    },
}

MAPIT_BASE_URL = 'http://mapit.staging.mysociety.org/'

