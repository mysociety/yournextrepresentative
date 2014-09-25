# All actions taken by this front-end can be seen as person-centric.
# We use an intermediate representation (a Python dictionary) of what
# that person and their membership should look like - all views that
# need to make a change to information about a person should generate
# data in this format.
#
# These functions takes a such a dictionary and either (a) change the
# person and their memberships to match or (b) creating the person
# from this data.
#
# The dictionary represents everything we're interested in about a
# candidate's status.  It may have the following fields, which are
# straighforward and set to the empty string if unknown.
#
#   'id'
#   'full_name'
#   'email'
#   'date_of_birth'
#   'wikipedia_url'
#   'homepage_url'
#   'twitter_username'
#
# It should also have a 'party_memberships' member which is set to a
# dictionary.  If someone was known to be standing for the
# Conservatives in 2010 and UKIP in 2015, this would be:
#
#   'party_memberships': {
#     '2010': {
#       'name': 'Conservative Party',
#       'id': 'conservative-party',
#     '2015': {
#       'name': 'UK Independence Party - UKIP',
#       'id': 'uk-independence-party-ukip',
#     }
#   }
#
# If someone is standing in 2015 for Labour, but wasn't standing in
# 2010, this should be:
#
#   'party_memberships': {
#     '2015': {
#       'name': 'Labour Party',
#       'id': 'labour-party',
#   }
#
# The 'id' field for a party is optional, since if you're using this
# representation to create a new party, you won't know it anyway.
#
# Finally, there is a 'standing_in' member which indicates if a person if
# known to be standing in 2010 or 2015:
#
# If someone was standing in 2010 in South Cambridgeshire, but nothing
# is known about 2015, this would be:
#
#   'standing_in': {
#     '2010': {
#       'name': 'South Cambridgeshire',
#       'mapit_url': 'http://mapit.mysociety.org/area/65922',
#     }
#   }
#
# If someone was standing in 2010 in Aberdeen South but is known not
# to be standing in 2015, this would be:
#
#   'standing_in': {
#     '2010': {
#        'name': 'Aberdeen South',
#        'mapit_url': 'http://mapit.mysociety.org/area/14399',
#     }
#     '2015': None,
#   }
#
# If someone was standing in Edinburgh East in 2010, but nothing is
# known about whether they're standing in 2015, this would be:
#
#   'standing_in': {
#     '2010': {
#        'name': 'Aberdeen South',
#        'mapit_url': 'http://mapit.mysociety.org/area/14399',
#     },
#   }
#
# Or if someone is known to be standing in Edinburgh East in 2010 and
# then is thought to be standing in Edinburgh North and Leith in 2015,
# this would be:
#
#   'standing_in': {
#     '2010': {
#        'name': 'Edinburgh East',
#        'mapit_url': 'http://mapit.mysociety.org/area/14419',
#     },
#     '2015': {
#        'name': 'Edinburgh North and Leith',
#        'mapit_url': 'http://mapit.mysociety.org/area/14420',
#     },
#   }

from collections import defaultdict
from datetime import timedelta, date
import json
import re
import time

from slugify import slugify

from slumber.exceptions import HttpClientError, HttpServerError

from .models import PopItPerson
from .models import MapItData
from .models import get_person_data_from_dict, update_id
from .models import simple_fields, complex_fields_locations, all_fields

from .models import election_date_2005, election_date_2010
from .models import candidate_list_name_re
from .models import get_candidate_list_popit_id
from .models import create_with_id_retries

def election_year_to_party_dates(election_year):
    if str(election_year) == '2010':
        return {
            'start_date': str(election_date_2005 + timedelta(days=1)),
            'end_date': str(election_date_2010),
        }
    elif str(election_year) == '2015':
        return {
            'start_date': str(election_date_2010 + timedelta(days=1)),
            'end_date': '9999-12-31',
        }
    else:
        raise Exception('Unknown election year: {0}'.format(election_year))

def get_value_from_location(location, person_data):
    found = False
    for info in person_data[location['sub_array']]:
        if info[location['info_type_key']] == location['info_type']:
            return info.get(location['info_value_key'], '')
    return ''

def reduced_organization_data(organization):
    return {
        'id': organization['id'],
        'name': organization['name'],
    }

def decompose_candidate_list_name(candidate_list_name):
    m = candidate_list_name_re.search(candidate_list_name)
    if not m:
        message = "Malformed candidate list name found: {0}"
        raise Exception(message.format(candidate_list_name))
    constituency_name, year = m.groups()
    mapit_data = MapItData.constituencies_2010_name_map.get(constituency_name)
    if mapit_data is None:
        message = "Couldn't find the constituency: '{0}'"
        raise Exception(message.format(constituency_name))
    url_format = 'http://mapit.mysociety.org/area/{0}'
    return {
        'year': year,
        'name': constituency_name,
        'mapit_url': url_format.format(mapit_data['id'])
    }

def get_standing_in_from_candidate_lists(candidate_list_organizations):
    result = {}
    for organization in candidate_list_organizations:
        cons_data = decompose_candidate_list_name(organization['name'])
        year = cons_data.pop('year')
        if year in result:
            message = "Someone found standing in multiple {0} constituencies: {1} and {2}"
            raise Exception(message.format(
                year,
                result[year]['name'],
                cons_data['name'],
            ))
        result[year] = cons_data
    return result

def get_year_party_map(party_memberships):
    year_to_memberships = defaultdict(list)
    for membership, organization in party_memberships:
        election_identified = False
        for election_date in (election_date_2005, election_date_2010):
            date_info = membership.get('start_date') or membership.get('end_date')
            if date_info and membership_covers_date(membership, election_date):
                year_to_memberships[str(election_date.year)].append(organization)
                election_identified = True
        if not election_identified:
            year_to_memberships[None].append(organization)
    ambiguous_years = dict(
        (year, parties) for year, parties in year_to_memberships.items()
        if len(parties) > 1
    )
    # Various checks that the data in PopIt hasn't been made
    # inconsistent (presumably by editing in the PopIt web UI):
    if ambiguous_years:
        raise Exception("Ambigous party data found: {0}".format(ambiguous_years))
    result = dict(
        (year, reduced_organization_data(parties[0]))
        for year, parties in year_to_memberships.items()
    )
    return result

def complete_partial_date(iso_8601_date_partial, start=True):
    """If we have a partial date string, complete it for range comparisons

    If 'start' is true, then fill in month and date parts with values
    that are as early as possible; if it's false make them as late as
    possible.  For example:

    >>> complete_partial_date('2001', True)
    '2001-01-01'
    >>> complete_partial_date('2001', False)
    '2001-12-31'
    >>> complete_partial_date('1970-04', True)
    '1970-04-01'
    >>> complete_partial_date('1970-04', False)
    '1970-04-31'
    >>> complete_partial_date('2014-09-21', True)
    '2014-09-21'
    >>> complete_partial_date('2014-09-21', False)
    '2014-09-21'

    """

    if start:
        default_month = '01'
        default_day = '01'
    else:
        default_month = '12'
        default_day = '31'
    if re.search(r'^\d{4}$', iso_8601_date_partial):
        return '{0}-{1}-{2}'.format(iso_8601_date_partial, default_month, default_day)
    elif re.search(r'^\d{4}-\d{2}$', iso_8601_date_partial):
        return '{0}-{1}'.format(iso_8601_date_partial, default_day)
    elif re.search(r'^\d{4}-\d{2}-\d{2}$', iso_8601_date_partial):
        return iso_8601_date_partial
    else:
        raise Exception, "Unknown partial ISO 8601 data format: {0}".format(iso_8601_date_partial)

def membership_covers_date(membership, date):
    """See if the dates in a membership cover a particular date

    For example:

    >>> membership_covers_date({
    ...     'start_date': '2010',
    ...     'end_date': '2015-01-01',
    ... }, date(2010, 5, 6))
    True

    >>> membership_covers_date({
    ...     'start_date': '2010-08',
    ...     'end_date': '2015',
    ... }, date(2010, 5, 6))
    False

    If a start date is missing, assume it's 'since forever' and if an
    end date is missing, assume it's 'until forever':

    >>> membership_covers_date({'end_date': '2014'}, date(2010, 5, 6))
    True
    >>> membership_covers_date({'end_date': '2010-03'}, date(2010, 5, 6))
    False
    >>> membership_covers_date({'start_date': '2014'}, date(2010, 5, 6))
    False
    >>> membership_covers_date({'start_date': '1976'}, date(2010, 5, 6))
    True
    >>> membership_covers_date({}, date(2010, 5, 6))
    True
    """

    start_date = membership.get('start_date')
    if not start_date:
        start_date = '0001-01-01'
    end_date = membership.get('end_date')
    if not end_date:
        end_date = '9999-12-31'
    start_date = complete_partial_date(start_date)
    end_date = complete_partial_date(end_date)
    return start_date <= str(date) and end_date >= str(date)

class PersonParseMixin(object):

    """A mixin for turning PopIt data into our representation

    This mixin depends on self.api being usable (it's provided in
    PopItApiMixin).

    FIXME: one could (and should) write tests for these methods
    """

    def get_person(self, person_id):
        """Get our representation of the candidate's data from a PopIt person ID"""

        result = {'id': person_id}
        person = PopItPerson.create_from_popit(self.api, person_id)
        for field in simple_fields:
            result[field] = person.popit_data.get(field, '')
        for field, location in complex_fields_locations.items():
            result[field] = get_value_from_location(location, person.popit_data)
        result['versions'] = person.popit_data.get('versions', [])

        # We'll need details of party memberships and candidate lists
        # from PopIt:
        popit_party_memberships = []
        popit_candidate_list_organizations = []
        for membership, organization in person.party_and_candidate_lists_iter():
            if organization['classification'] == 'Party':
                popit_party_memberships.append((membership, organization))
            elif organization['classification'] == 'Candidate List':
                popit_candidate_list_organizations.append(organization)
            else:
                raise Exception("An unexpected organization classification {} was returned by party_and_candidate_lists_iter")

        # First, get all the information we can from the candidate
        # list memberships:
        standing_in = get_standing_in_from_candidate_lists(
            popit_candidate_list_organizations
        )

        # However, we can't infer from the candidate lists that
        # someone's a member of that we know that they're known not to
        # be standing in a particular election. So, if that
        # information is present in the PopIt data, set it in the
        # standing_in dictionary.
        for year, standing in person.popit_data.get('standing_in', {}).items():
            if standing:
                # Then there must already be a corresponding candidate
                # list membership, but check that:
                if year not in standing_in:
                    message = "Missing Candidate List membership according to PopIt data for {} in {}"
                    # raise Exception(message.format(person_id, year))
            else:
                standing_in[year] = None

        # Now consider the party memberships:
        year_to_party = get_year_party_map(popit_party_memberships)
        party_memberships = {}
        for year, standing in standing_in.items():
            party = year_to_party.get(year)
            party_2010 = year_to_party.get('2010')
            fallback_party = year_to_party.get(None)
            if party:
                party_memberships[year] = party
            elif fallback_party:
                party_memberships[year] = fallback_party
            elif year == '2015' and party_2010:
                party_memberships[year] = party_2010
            else:
                message = "There was no party data for {0} in {1}"
                raise Exception, message.format(person_id, year)

        result['standing_in'] = standing_in
        result['party_memberships'] = party_memberships
        return result


class PersonUpdateMixin(object):
    """A mixin for updating PopIt from our representation

    This mixin depends on the following being usable:
        self.api (from PopItApiMixin)
        self.create_membership (from PopItApiMixin)
        self.get_party (from CandidacyMixin)

    FIXME: it'd be good to have tests for this, but it's non-obvious
    how to write them without creating a fresh PopIt instance to run
    them against.
    """

    def create_party_memberships(self, person_id, data):
        for election_year, party in data.get('party_memberships', {}).items():
            popit_party = self.get_party(party['name'])
            if not popit_party:
                # Then create a new party:
                popit_party = party.copy()
                popit_party['classification'] = 'Party'
                result = self.api.organizations.post(popit_party)
                popit_party = result['result']
            # Create the party membership:
            membership = election_year_to_party_dates(election_year)
            membership['person_id'] = person_id
            membership['organization_id'] = popit_party['id']
            self.create_membership(**membership)

    def create_candidate_list_memberships(self, person_id, data):
        for election_year, constituency in data.get('standing_in', {}).items():
            if constituency:
                # i.e. we know that this isn't an indication that the
                # person isn't standing...
                name = constituency['name']
                mapit_url = constituency['mapit_url']
                # Create the candidate list membership:
                membership = election_year_to_party_dates(election_year)
                membership['person_id'] = person_id
                membership['organization_id'] = \
                    get_candidate_list_popit_id(name, election_year)
                self.create_membership(**membership)

    def create_person(self, data, change_metadata):
        # Create the person:
        basic_person_data = get_person_data_from_dict(data, generate_id=True)
        basic_person_data['standing_in'] = data['standing_in']
        basic_person_data['id'] = slugify(basic_person_data['name'])
        version = change_metadata.copy()
        version['data'] = data
        basic_person_data['versions'] = [version]
        person_result = create_with_id_retries(self.api.persons, basic_person_data)
        person_id = person_result['result']['id']
        self.create_party_memberships(person_id, data)
        self.create_candidate_list_memberships(person_id, data)

    def update_person(self, data, change_metadata, previous_versions):
        person_id = data['id']
        basic_person_data = get_person_data_from_dict(data, generate_id=False)
        basic_person_data['standing_in'] = data['standing_in']
        new_version = change_metadata.copy()
        new_version['data'] = data
        basic_person_data['versions'] = [new_version] + previous_versions
        print "putting basic_person_data:", json.dumps(basic_person_data, indent=4)
        person_result = self.api.persons(person_id).put(basic_person_data)

        # XXX FIXME: Horrible hack until
        # https://github.com/mysociety/popit/issues/631 is understood
        # and fixed.
        time.sleep(0.5)

        person = PopItPerson.create_from_popit(self.api, data['id'])

        # Now remove any party or candidate list memberships; this
        # leaves any other memberships someone might have added.
        print "### considering deletions:"
        for membership, o in person.party_and_candidate_lists_iter():
            print "### deleting membership of:", o['name']
            self.api.memberships(membership['id']).delete()

        # And then create any that should be there:
        self.create_party_memberships(person_id, data)
        self.create_candidate_list_memberships(person_id, data)
