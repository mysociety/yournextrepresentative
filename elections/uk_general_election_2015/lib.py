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
