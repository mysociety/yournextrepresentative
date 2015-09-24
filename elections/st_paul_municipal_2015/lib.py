import re
import os
import json

from candidates.static_data import (
    BaseMapItData, BasePartyData, BaseAreaPostData
)

class MapItData(BaseMapItData):
    pass


class PartyData(BasePartyData):

    def __init__(self):
        super(PartyData, self).__init__()
        self.ALL_PARTY_SETS = (
            {'slug': 'st-paul', 'name': 'Saint Paul, Minnesota'},
        )

    def party_data_to_party_sets(self, party_data):
        return ['st-paul']

class AreaPostData(BaseAreaPostData):

    def shorten_post_label(self, election, post_label):
        return re.sub(r'^Council Member for ', '', post_label)

    def area_to_post_group(self, area_data):
        return area_data['country_name']

    def post_id_to_party_set(self, post_id):
        return 'st-paul'


EXTRA_CSV_ROW_FIELDS = [
    'gss_code',
    'parlparse_id',
    'theyworkforyou_url',
    'party_ec_id',
]

def get_extra_csv_values(person, election, mapit_data):
    theyworkforyou_url = None
    parlparse_id = person.get_identifier('uk.org.publicwhip')
    if parlparse_id:
        m = re.search(r'^uk.org.publicwhip/person/(\d+)$', parlparse_id)
        if not m:
            message = "Malformed parlparse ID found {0}"
            raise Exception, message.format(parlparse_id)
        parlparse_person_id = m.group(1)
        theyworkforyou_url = 'http://www.theyworkforyou.com/mp/{0}'.format(
            parlparse_person_id
        )
    party_ec_id = person.parties[election].get('electoral_commission_id', '')

    return {
        'gss_code': mapit_data.areas_by_id[('WMC', 22)][
            person.standing_in[election]['post_id']
        ]['codes']['gss'],
        'parlparse_id': parlparse_id,
        'theyworkforyou_url': theyworkforyou_url,
        'party_ec_id': party_ec_id
    }
