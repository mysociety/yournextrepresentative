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
#       'id': 'party:52',
#     '2015': {
#       'name': 'UK Independence Party - UKIP',
#       'id': 'party:85',
#     }
#   }
#
# If someone is standing in 2015 for Labour, but wasn't standing in
# 2010, this should be:
#
#   'party_memberships': {
#     '2015': {
#       'name': 'Labour Party',
#       'id': 'party:52',
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

from datetime import timedelta

from .models import PopItPerson
from .static_data import MapItData, PartyData
from .models import get_person_data_from_dict
from .models import simple_fields, complex_fields_locations

from .models import election_date_2005, election_date_2010
from .models import candidate_list_name_re
from .models import create_person_with_id_retries

from .popit import PopItApiMixin

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

class PersonParseMixin(PopItApiMixin):

    """A mixin for turning PopIt data into our representation"""

    def get_person(self, person_id):
        """Get our representation of the candidate's data from a PopIt person ID"""

        result = {'id': person_id}
        person = PopItPerson.create_from_popit(self.api, person_id)
        for field in simple_fields:
            result[field] = person.popit_data.get(field, '')
        for field, location in complex_fields_locations.items():
            result[field] = get_value_from_location(location, person.popit_data)
        result['versions'] = person.popit_data.get('versions', [])

        year_to_party = person.parties
        standing_in = person.standing_in
        party_memberships = {}
        for year, standing in standing_in.items():
            party = year_to_party.get(year)
            party_2010 = year_to_party.get('2010')
            fallback_party = year_to_party.get(None)
            if party:
                party_memberships[year] = reduced_organization_data(party)
            elif fallback_party:
                party_memberships[year] = reduced_organization_data(fallback_party)
            elif year == '2015' and party_2010:
                party_memberships[year] = reduced_organization_data(party_2010)
            else:
                message = "There was no party data for {0} in {1}"
                raise Exception, message.format(person_id, year)

        result['standing_in'] = standing_in
        result['party_memberships'] = party_memberships
        return result


class PersonUpdateMixin(PopItApiMixin):
    """A mixin for updating PopIt from our representation"""

    def create_party_memberships(self, person_id, data):
        for election_year, party in data.get('party_memberships', {}).items():
            if party['id'] not in PartyData.party_id_to_name:
                msg = "Couldn't create party memberships for unknown ID {0}"
                raise Exception, msg.format(party['id'])
            # Create the party membership:
            membership = election_year_to_party_dates(election_year)
            membership['person_id'] = person_id
            membership['organization_id'] = party['id']
            self.create_membership(**membership)

    def create_candidate_list_memberships(self, person_id, data):
        for election_year, constituency in data.get('standing_in', {}).items():
            if constituency:
                # i.e. we know that this isn't an indication that the
                # person isn't standing...
                # Create the candidate list membership:
                membership = election_year_to_party_dates(election_year)
                membership['person_id'] = person_id
                membership['post_id'] = constituency['post_id']
                membership['role'] = "Candidate"
                self.create_membership(**membership)

    def create_person(self, data, change_metadata):
        # Create the person:
        basic_person_data = get_person_data_from_dict(data, generate_id=True)
        basic_person_data['standing_in'] = data['standing_in']
        original_version = change_metadata.copy()
        original_version['data'] = data
        person_result = create_person_with_id_retries(
            self.api,
            basic_person_data,
            original_version
        )
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
        self.api.persons(person_id).put(basic_person_data)

        person = PopItPerson.create_from_popit(self.api, data['id'])
        person.delete_memberships()

        # And then create any that should be there:
        self.create_party_memberships(person_id, data)
        self.create_candidate_list_memberships(person_id, data)
