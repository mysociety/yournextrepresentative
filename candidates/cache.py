POSTS_CACHE = {}
PERSON_TO_POSTS_CACHE = {}

def invalidate_person(person_id):
    if person_id in PERSON_TO_POSTS_CACHE:
        mapit_area_id = PERSON_TO_POSTS_CACHE[person_id]
        POSTS_CACHE.pop(mapit_area_id, None)
        PERSON_TO_POSTS_CACHE.pop(person_id, None)

def cache_posts(api, mapit_area_id):
    if mapit_area_id in POSTS_CACHE:
        return POSTS_CACHE[mapit_area_id]

    mp_post = api.posts(mapit_area_id).get(
        embed='membership.person.membership.organization')
    POSTS_CACHE[mapit_area_id] = mp_post

    for membership in mp_post['result']['memberships']:
        person_id = membership['person_id']['id']
        PERSON_TO_POSTS_CACHE[person_id] = mapit_area_id

    return mp_post
