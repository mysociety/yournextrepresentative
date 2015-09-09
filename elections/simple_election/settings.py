from datetime import date

# settings for each election:
# ---------------------------
#
# Some of these settings are straightforward. Others are more
# subtle: some of the start and end dates are needed to make
# sure the candidates are returned by searches made using the
# PopIt API for dates within this election. This can matter
# if the data ends up in a database with data from previous
# or subsequent elections.
# See the following notes for any settings you're not sure about.
#--------------------------------------------------------------

# name:
#    The name of the election
#
# for_post_role:
#    The name of the post or role candidates are hoping
#    to be elected for.
#    For example:
#        'Member of Parliament'
#
# candidate_membership_role:
#    The description of the role.
#    For example:
#         'Candidate'
#
# winner_membership_role:
#    The name of the role that a winner of this election will have.
#    Sometimes the winner of an election simply gets the for_post_role,
#    in which case winner_membership_role isn't needed (and can be None).
#    But some elections are to selected candidates for a secondary vote
#    in which case the winner_membership_role is not the same as the ultimate
#    role.
#    For example:
#        None
#    or
#       'Primary candidate
#
# election_date:
#    The date when the election will happen.
#
# candidacy_start_date:
#    The date when the candidate became available for election; this may well
#    be the start date of the election. This is useful for PopIt API searches, 
#    because it allows searches for an election that was active for a specific
#    date.
#
# organization_id:
#    A post in Popolo must belong to an organisation. Typically the organisation
#    will typically be the body to which candidates are trying to be elected.
#    e.g. House of Representatives, National Assembly, Senate, etc
#
# current:
#    Set to True if the election is forthcoming or active now (rather than
#    historic)
#
# party_membership_start_date:
# party_membership_end_date:
#    A candidate is automatically a member of a the party they are standing for,
#    but PopIt searches work best if there's a start and end date of that 
#    membership. In practice it's rare to know when someone's party membership
#    actually started, so we recommend setting memebership to be for the period
#    you *do* know about: the day after the last election to the day of the
#    election for which they are a candidate.
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
#    If the election is for a whole country, use a fixed string
#    (like "country"). But if it's by consitituency, for example,
#    use "{area_id}". This is a Python string so that will be
#    replaced with the area_id, which will typically be the 
#    constituency name.

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
