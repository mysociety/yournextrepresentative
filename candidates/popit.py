from django.conf import settings

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
