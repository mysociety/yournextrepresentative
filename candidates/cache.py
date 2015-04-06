from django.core.cache import cache

def person_to_post_cache_key(person_id):
    return "person-to-post:{0}".format(person_id)

def post_cache_key(mapit_area_id):
    return "post:{0}".format(mapit_area_id)

def invalidate_person(person_id):
    person_key = person_to_post_cache_key(person_id)
    mapit_area_id = cache.get(person_key)
    if mapit_area_id is not None:
        post_key = post_cache_key(mapit_area_id)
        cache.delete(post_key)
        cache.delete(person_key)

def cache_posts(api, mapit_area_id):
    post_key = post_cache_key(mapit_area_id)
    result_from_cache = cache.get(post_key)
    if result_from_cache is not None:
        return result_from_cache

    mp_post = api.posts(mapit_area_id).get(
        embed='membership.person.membership.organization')
    cache.set(post_key, mp_post, None)

    for membership in mp_post['result']['memberships']:
        person_id = membership['person_id']['id']
        person_key = person_to_post_cache_key(person_id)
        cache.set(person_key, mapit_area_id, None)

    return mp_post
