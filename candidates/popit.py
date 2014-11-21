from urlparse import urlunsplit

from django.conf import settings
from django.utils.http import urlquote

from popit_api import PopIt

def create_popit_api_object():
    api_properties = {
        'instance': settings.POPIT_INSTANCE,
        'hostname': settings.POPIT_HOSTNAME,
        'port': settings.POPIT_PORT,
        'api_version': 'v0.1',
        'append_slash': False,
    }
    if settings.POPIT_API_KEY:
        api_properties['api_key'] = settings.POPIT_API_KEY
    else:
        api_properties['user'] = settings.POPIT_USER
        api_properties['password'] = settings.POPIT_PASSWORD
    return PopIt(**api_properties)

def popit_unwrap_pagination(api_collection, **kwargs):
    page = 1
    keep_fetching = True
    while keep_fetching:
        get_kwargs = {
            'per_page': 50,
            'page': page,
        }
        get_kwargs.update(kwargs)
        response = api_collection.get(**get_kwargs)
        keep_fetching = response.get('has_more', False)
        page += 1
        for api_object in response['result']:
            yield api_object

class PopItApiMixin(object):

    """This provides helper methods for manipulating data in a PopIt instance"""

    def __init__(self, *args, **kwargs):
        super(PopItApiMixin, self).__init__(*args, **kwargs)
        self.api = create_popit_api_object()

    def get_base_url(self):
        port = settings.POPIT_PORT
        instance_hostname = settings.POPIT_INSTANCE + \
            '.' + settings.POPIT_HOSTNAME
        if port != 80:
            instance_hostname += ':' + str(port)
        base_url = urlunsplit(
            ('http', instance_hostname, '/api/v0.1/', '', '')
        )
        return base_url

    def get_search_url(self, collection, query, **kwargs):
        base_search_url = self.get_base_url() + 'search/'
        parameters = {
            'q': query,
        }
        parameters.update(kwargs)
        query_string = '&'.join(
            k + '=' + urlquote(v) for k, v in parameters.items()
        )
        return base_search_url + collection + '?' + query_string

    def create_membership(self, person_id, **kwargs):
        '''Create a membership of a post or an organization'''
        properties = {
            'person_id': person_id,
        }
        for key, value in kwargs.items():
            if value is not None:
                properties[key] = value
        self.api.memberships.post(properties)
