from django.core.cache import cache

def post_cache_key(mapit_area_id):
    """Form the cache key used for post data"""
    return "post:{0}".format(mapit_area_id)

def invalidate_posts(post_ids):
    for post_id in post_ids:
        post_key = post_cache_key(post_id)
        cache.delete(post_key)

def get_post_cached(api, mapit_area_id):
    post_key = post_cache_key(mapit_area_id)
    result_from_cache = cache.get(post_key)
    if result_from_cache is not None:
        return result_from_cache

    mp_post = api.posts(mapit_area_id).get(
        embed='membership.person.membership.organization')
    cache.set(post_key, mp_post, None)

    return mp_post
