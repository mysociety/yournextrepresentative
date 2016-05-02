from django.conf import settings
from django.core.cache import cache
from django.utils.six import text_type

import requests

from popolo.models import ContactDetail


class TwitterAPITokenMissing(Exception):
    pass


def get_twitter_user_id(twitter_screen_name):
    cache_key = 'twitter-screen-name:{0}'.format(twitter_screen_name)
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    token = settings.TWITTER_APP_ONLY_BEARER_TOKEN
    if not token:
        raise TwitterAPITokenMissing()
    headers = {'Authorization': 'Bearer {token}'.format(token=token)}
    r = requests.post(
        'https://api.twitter.com/1.1/users/lookup.json',
        data={'screen_name': twitter_screen_name},
        headers=headers,
    )
    data = r.json()
    if data:
        if 'errors' in data:
            all_errors = data['errors']
            if any(d['code'] == 17 for d in all_errors):
                # (That's the error code for not being able to find the
                # user.)
                result = ''
            else:
                raise Exception("The Twitter API says: {error_messages}".format(
                    error_messages=data['errors']
                ))
        else:
            result = text_type(data[0]['id'])
    else:
        result = ''
    # Cache Twitter screen name -> user ID results for 5 minutes -
    # this is largely so we usually only make one API call for both
    # validating a screen name in a form and acting on submission of
    # that form.
    cache.set(cache_key, result, 60 * 5)
    return result

def update_twitter_user_id(person):
    try:
        screen_name = person.contact_details \
            .get(contact_type='twitter').value
    except ContactDetail.DoesNotExist:
        return
    user_id = get_twitter_user_id(screen_name)
    if not user_id:
        return
    person.identifiers.update_or_create(
        scheme='twitter',
        defaults={'identifier': user_id}
    )
