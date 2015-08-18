from datetime import date

# settings for each election:
# ---------------------------
#
# name:
#    The name of the election
#
# for_post_role:
#    The name of the post or role candidates are hoping
#    to be elected for.
#    For example: 'Member of Parliament'
#
# candidate_membership_role:
#    The description of the role.
#
# winner_membership_role:
#    FIXME
#
# election_date:
#    The date when the election will happen.
#
# candidacy_start_date:
#    The date when the elected representatives
#
# organization_id:
#    FIXME mapping
#
# current:
#    Set to True if the election is forthcoming 
#    (rather than historic)
#
# party_membership_start_date:
# party_membership_end_date:
#    FIXME
#
# mapit_types:
# mapit_generation:
#    These settings to identify the areas within MapIt
#    that are constituency areas.
#    See also MAPIT_BASE_URL below.
#    Boundary data often changes, especially from one
#    election to another, so MapIt distinguishes between
#    sets of data using generations. Specify the generation
#    that this election is locked onto (so if area data 
#    changes, it won't affect YourNextRepresentative.)
#
# post_id_format:
#    FIXME

ELECTIONS = {
    '2015': {
        'for_post_role': 'Member of Parliament',
        'candidate_membership_role': 'Candidate',
        'winner_membership_role': None,
        'election_date': date(2015, 1, 31),
        'candidacy_start_date': date(2010, 1, 31),
        'organization_id': 'national_parliament',
        'name': '2015 National Election',
        'current': True,
        'party_membership_start_date': date(2015, 1, 31),
        'party_membership_end_date': date(9999, 12, 31),
        'mapit_types': ['WMC'],
        'mapit_generation': 22,
        'post_id_format': '{area_id}',
    }
}

MAPIT_BASE_URL = 'http://mapit.mysociety.org/'
