from __future__ import print_function, unicode_literals

from django.conf import settings
from django.utils.six import text_type
from django.utils.translation import ugettext as _

from popolo.models import ContactDetail, Identifier
import requests


def none_found_error(parsed_result):
    msg = "Unknown error from the Twitter API: {0}"
    if 'errors' not in parsed_result:
        return False
    errors = parsed_result['errors']
    if len(errors) != 1:
        raise Exception(msg.format(errors))
    error = errors[0]
    if error['code'] == 17:
        return True
    raise Exception(msg.format(errors))


class TwitterAPIData(object):

    MAX_IN_A_REQUEST = 100

    def __init__(self):
        self.token = settings.TWITTER_APP_ONLY_BEARER_TOKEN
        if not self.token:
            raise Exception(_("TWITTER_APP_ONLY_BEARER_TOKEN was not set"))
        self.headers = {
            'Authorization': 'Bearer {token}'.format(token=self.token)
        }
        self.screen_name_to_user_id = {}
        self.user_id_to_screen_name = {}
        self.user_id_to_photo_url = {}

    def update_id_mapping(self, data):
        user_id = text_type(data['id'])
        screen_name = data['screen_name']
        self.screen_name_to_user_id[screen_name.lower()] = user_id
        self.user_id_to_screen_name[user_id] = screen_name
        self.user_id_to_photo_url[user_id] = data['profile_image_url_https']

    def update_from_api(self):
        for data in self.twitter_results('screen_name', self.all_screen_names):
            self.update_id_mapping(data)
        # Now look for any user IDs in the database that weren't found
        # from the above query:
        remaining_user_ids = list(
            set(self.all_user_ids) - set(self.user_id_to_screen_name.keys())
        )
        for data in self.twitter_results('user_id', remaining_user_ids):
            self.update_id_mapping(data)

    @property
    def all_screen_names(self):
        '''Find all unique Twitter screen names in the database'''
        return set(
            ContactDetail.objects.filter(contact_type='twitter'). \
            values_list('value', flat=True)
        )

    @property
    def all_user_ids(self):
        '''Find all unique Twitter identifiers in the database'''
        return set(
            Identifier.objects.filter(scheme='twitter'). \
                values_list('identifier', flat=True)
        )

    def twitter_results(self, key, values):
        sorted_values = sorted(values)
        for i in range(0, len(sorted_values), self.MAX_IN_A_REQUEST):
            some_values = sorted_values[i:(i + self.MAX_IN_A_REQUEST)]
            r = requests.post(
                'https://api.twitter.com/1.1/users/lookup.json',
                data={
                    key: ','.join(some_values)
                },
                headers=self.headers,
            )
            parsed_result = r.json()
            if not none_found_error(parsed_result):
                for data in parsed_result:
                    yield data
