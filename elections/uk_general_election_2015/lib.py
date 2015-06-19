import re

from candidates.static_data import (
    BaseMapItData, BasePartyData, BaseAreaPostData
)

class MapItData(BaseMapItData):
    pass


class PartyData(BasePartyData):

    def __init__(self):
        super(PartyData, self).__init__()
        self.ALL_PARTY_SETS = (
            {'slug': 'gb', 'name': 'Great Britain'},
            {'slug': 'ni', 'name': 'Northern Ireland'},
        )

    def party_data_to_party_sets(self, party_data):
        register = {
            'Great Britain': 'gb',
            'Northern Ireland': 'ni',
        }.get(party_data.get('register'))
        if register:
            return [register]
        else:
            # There are some pseudo-parties, like 'Independent' or
            # 'Speaker seeking re-election' which won't have a register,
            # so we add them to all party sets.
            return ['gb', 'ni']


class AreaPostData(BaseAreaPostData):

    def __init__(self, *args, **kwargs):
        super(AreaPostData, self).__init__(*args, **kwargs)
        self.ALL_POSSIBLE_POST_GROUPS = [
            'England', 'Northern Ireland', 'Scotland', 'Wales'
        ]

    def area_to_post_group(self, area_data):
        return area_data['country_name']

    def get_post_id(self, mapit_type, area_id):
        return str(area_id)

    def post_id_to_party_set(self, post_id):
        area = self.areas_by_post_id[post_id]
        if area['country_name'] == 'Northern Ireland':
            return 'ni'
        else:
            return 'gb'

    def post_id_to_post_group(self, election, post_id):
        # In the UK, the post IDs are the same as MapIt IDs,
        # so just look it up from the MapIt data:
        areas_by_id = self.mapit_data.areas_by_id[('WMC', 22)]
        area = areas_by_id.get(post_id)
        return area['country_name']

    def shorten_post_label(self, election, post_label):
        return re.sub(r'^Member of Parliament for ', '', post_label)

    def party_to_possible_post_groups(self, party_data):
        register = party_data.get('register')
        if register == 'Northern Ireland':
            return ('Northern Ireland',)
        elif register == 'Great Britain':
            return ('England', 'Scotland', 'Wales')
        else:
            return ('England', 'Northern Ireland', 'Scotland', 'Wales')
