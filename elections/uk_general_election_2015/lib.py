ALL_POSSIBLE_PARTY_POST_GROUPS = [
    'England', 'Northern Ireland', 'Scotland', 'Wales'
]

def party_to_possible_post_groups(party_data):
    register = party_data.get('register')
    if register == 'Northern Ireland':
        return ('Northern Ireland',)
    elif register == 'Great Britain':
        return ('England', 'Scotland', 'Wales')
    else:
        return ('England', 'Northern Ireland', 'Scotland', 'Wales')

def area_to_post_group(area_data):
    return area_data['country_name']

party_sets = (
    {'slug': 'gb', 'name': 'Great Britain'},
    {'slug': 'ni', 'name': 'Northern Ireland'},
)

def post_id_to_party_set(post_id):
    # Avoid a circular import dependency; it would be better to
    # restructured the imports to avoid this, so this is just a
    # workaround (FIXME)
    from candidates.static_data import MapItData
    area = MapItData.areas_by_post_id[post_id]
    if area['country_name'] == 'Northern Ireland':
        return 'ni'
    else:
        return 'gb'
