from candidates.static_data import (
    BaseMapItData, BasePartyData, BaseAreaPostData
)


class MapItData(BaseMapItData):
    pass


def index_lambda(sequence, predicate):
    for i, item in enumerate(sequence):
        if predicate(item):
            return i
    return -1

def move_to_front(l, predicate):
    i = index_lambda(l, lambda x: predicate(x))
    l.insert(0, l.pop(i))


class PartyData(BasePartyData):

    def __init__(self):
        super(PartyData, self).__init__()
        self.ALL_PARTY_SETS = (
            {'slug': 'nacionale', 'name': 'Nacionale'},
        )

    def party_data_to_party_sets(self, party_data):
        return ['nacionale']

    def sort_parties_in_place(self, parties):
        parties.sort(key=lambda p: p[1].lower())
        # Then we need 'unknown' and 'not listed' at the top:
        move_to_front(parties, lambda x: x[0] == 'not-listed')
        move_to_front(parties, lambda x: x[0] == 'unknown')


class AreaPostData(BaseAreaPostData):

    def __init__(self, *args, **kwargs):
        super(AreaPostData, self).__init__(*args, **kwargs)
        self.ALL_POSSIBLE_POST_GROUPS = [None]

    def area_to_post_group(self, area_data):
        return None

    def post_id_to_party_set(self, post_id):
        return 'nacionale'

    def post_id_to_post_group(self, election, post_id):
        return None

    def shorten_post_label(self, election, post_label):
        return post_label

    def party_to_possible_post_groups(self, party_data):
        return (None,)
