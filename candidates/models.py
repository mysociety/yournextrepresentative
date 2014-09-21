import json
from os.path import dirname, join, abspath
import re
from slugify import slugify

from django.db import models

from slumber.exceptions import HttpServerError

data_directory = abspath(join(dirname(__file__), '..', 'data'))

simple_fields = ('name', 'email', 'date_of_birth')

complex_fields_locations = {
    'wikipedia_url': {
        'sub_array': 'links',
        'info_type_key': 'note',
        'info_value_key': 'url',
        'info_type': 'wikipedia',
    },
    'homepage_url': {
        'sub_array': 'links',
        'info_type_key': 'note',
        'info_value_key': 'url',
        'info_type': 'homepage',
    },
    'twitter_username': {
        'sub_array': 'contact_details',
        'info_type_key': 'type',
        'info_value_key': 'value',
        'info_type': 'twitter',
    },
}

all_fields = list(simple_fields) + complex_fields_locations.keys()

candidate_list_name_re = re.compile(r'^Candidates for (.*) in (\d+)$')

def get_mapit_constituencies(basename):
    with open(join(data_directory, basename)) as f:
        return json.load(f)

def get_constituency_name_map(basename):
    result = {}
    for constituency in get_mapit_constituencies(basename).values():
        result[constituency['name']] = constituency
    return result

class MapItData(object):
    constituencies_2010 = \
        get_mapit_constituencies('mapit-WMC-generation-13.json')
    constituencies_2010_name_map = \
        get_constituency_name_map('mapit-WMC-generation-13.json')

def get_mapit_id_from_mapit_url(mapit_url):
    m = re.search(r'http://mapit.mysociety.org/area/(\d+)', mapit_url)
    if not m:
        raise Exception("Failed to parse the MapIt URL: {0}".format(mapit_url))
    return m.group(1)

def get_next_id(current_id):
    """Increment the trailing digit in an ID

    For example:

    >>> get_next_id('foo-10')
    u'foo-11'
    >>> get_next_id('bar-')
    u'bar-1'
    >>> get_next_id('quux-13-20')
    u'quux-13-21'
    >>> get_next_id('john-smith')
    u'john-smith-1'
    """
    current_id = re.sub(r'-$', '', current_id)
    # If it ends in '-1', '-2', etc. then just increment that number,
    # otherwise assume it's the first numbered slug and add '-1'
    m = re.search(r'^(.*)-(\d+)$', current_id)
    if m:
        last_id = int(m.group(2), 10)
        return u'{0}-{1}'.format(m.group(1), last_id + 1)
    else:
        return u'{0}-1'.format(current_id)

def update_id(person_data):
    """Update the ID in person_data

    For example:

    >>> pd = {'id': 'john-smith', 'name': 'John Smith'}
    >>> update_id(pd)
    >>> json.dumps(pd, sort_keys=True)
    '{"id": "john-smith-1", "name": "John Smith"}'
    >>> update_id(pd)
    >>> json.dumps(pd, sort_keys=True)
    '{"id": "john-smith-2", "name": "John Smith"}'
    """
    person_data['id'] = get_next_id(person_data['id'])

def create_with_id_retries(api_collection, data):
    while True:
        try:
            result = api_collection.post(data)
            break
        except HttpServerError as hse:
            # Sometimes the ID that we try will be taken already, so
            # detect that case, otherwise just reraise the exception.
            error = json.loads(hse.content)
            if error.get('error', {}).get('code') == 11000:
                update_id(data)
                continue
            else:
                raise
    return result

def get_candidate_list_popit_id(constituency_name, year):
    """Return the PopIt organization ID for a constituency's candidate list

    >>> get_candidate_list_popit_id('Leeds North East', 2010)
    'candidates-2010-leeds-north-east'
    >>> get_candidate_list_popit_id('Ayr, Carrick and Cumnock', 2015)
    'candidates-2015-ayr-carrick-and-cumnock'
    """
    return 'candidates-{year}-{slugified_name}'.format(
        year=year,
        slugified_name=slugify(constituency_name),
    )

def extract_constituency_name(candidate_list_organization):
    """Return the constituency name from a candidate list organization

    >>> extract_constituency_name({
    ...     'name': 'Candidates for Altrincham and Sale West in 2015'
    ... })
    'Altrincham and Sale West'
    >>> constituency_name = extract_constituency_name({
    ...     'name': 'Another Organization'
    ... })
    >>> print constituency_name
    None
    """
    m = candidate_list_name_re.search(
        candidate_list_organization['name']
    )
    if m:
        return m.group(1)
    return None

def get_constituency_name_from_mapit_id(mapit_id):
    constituency_data = MapItData.constituencies_2010.get(str(mapit_id))
    if constituency_data:
        return constituency_data['name']
    return None

class PopItPerson(object):

    def __init__(self, api=None, popit_data=None):
        self.popit_data = popit_data
        self.api = api
        self.party = None
        self.constituency_2015 = None

    @classmethod
    def create_from_popit(cls, api, popit_person_id):
        popit_data = api.persons(popit_person_id).get()['result']
        new_person = cls(api=api, popit_data=popit_data)
        new_person._update_organizations()
        return new_person

    @property
    def name(self):
        return self.popit_data['name']

    @property
    def id(self):
        return self.popit_data['id']

    def _update_organizations(self):
        for m in self.popit_data.get('memberships', []):
            # FIXME: note that this fetches a huge object from the
            # API, since the organisation object for a party has a
            # list of all its memberships inline, which can be
            # hundreds of people for a major party. See the comment on
            # the related issue here:
            # https://github.com/mysociety/popit/issues/593#issuecomment-51690405
            o = self.api.organizations(m['organization_id']).get()['result']
            # FIXME: this is just quick and broken implementation -
            # it's obviously not correct, because if someone changes
            # parties between the 2010 and 2015 elections, they'll
            # have multiple party memberships, and this will pick one
            # at random.  However, at the moment there's no date
            # information for party memberships either, so let's deal
            # with that later.
            if o['classification'] == 'Party':
                self.party = o
            if o['classification'] == 'Candidate List' and re.search(r' 2015$', o['name']):
                self.constituency_2015 = o

    def get_candidate_list_memberships(self, year):
        # FIXME: this is hacky, but we can replace this easily after
        # https://github.com/mysociety/popit-api/pull/72 is merged and
        # there is full organization information in the memberships
        # array:
        return [
            m for m in self.popit_data.get('memberships', [])
            if re.search(r'^candidates-{}-'.format(year), m['id'])
        ]

    def get_party_memberships(self):
        # Similarly to the previous method, this should be rewritten
        # when that change is deployed:
        result = []
        for m in self.popit_data.get('memberships', []):
            o = self.api.organizations(m['organization_id']).get()['result']
            if o['classification'] == 'Party':
                result.append(m)
        return result

def update_values_in_sub_array(data, location, new_value):
    """Ensure that only a particular value is present in a sub-dict

    This is useful for replacing values nested in sub-objects of JSON
    data.  This is best demonstrated with an example: if we wanted to
    change the homepage URL in a person record, you could do it like
    this:

    >>> person_data = {
    ...     'id': "john-doe",
    ...     'name': "John Doe",
    ...     'email': "john-doe@example.org",
    ...     'links': [
    ...         {
    ...             'note': "wikipedia",
    ...             'url': "http://en.wikipedia.org/wiki/John_Doe"
    ...         },
    ...         {
    ...             'note': "homepage",
    ...             'url': "http://www.geocities.com"
    ...         },
    ...         {
    ...             'note': "homepage",
    ...             'url': "http://oops.duplicate.example.org"
    ...         }
    ...     ],
    ... }
    >>> update_values_in_sub_array(
    ...     person_data,
    ...     {'sub_array': 'links',
    ...      'info_type_key': 'note',
    ...      'info_value_key': 'url',
    ...      'info_type': 'homepage'},
    ...     "http://john.doe.example.org"
    ... )
    >>> print json.dumps(person_data, indent=4) # doctest: +NORMALIZE_WHITESPACE
    {
        "email": "john-doe@example.org",
        "id": "john-doe",
        "links": [
            {
                "note": "wikipedia",
                "url": "http://en.wikipedia.org/wiki/John_Doe"
            },
            {
                "note": "homepage",
                "url": "http://john.doe.example.org"
            }
        ],
        "name": "John Doe"
    }
    """
    new_info = [
        c for c in data.get(location['sub_array'], [])
        if c.get(location['info_type_key']) != location['info_type']
    ]
    new_info.append({
        location['info_type_key']: location['info_type'],
        location['info_value_key']: new_value
    })
    data[location['sub_array']] = new_info

def get_person_data_from_dict(data, generate_id, existing_data=None):
    if existing_data is None:
        result = {}
    else:
        result = existing_data
    # First deal with fields that simply map to top level fields in
    # Popolo.
    for field_name in simple_fields:
        if data[field_name]:
            result[field_name] = unicode(data[field_name])
    if generate_id:
        result['id'] = slugify(result['name'])
    # These are fields which are represented by values in a sub-object
    # in Popolo's JSON serialization:
    for field_name, location in complex_fields_locations.items():
        new_value = data[field_name]
        if new_value:
            update_values_in_sub_array(result, location, new_value)
    return result
