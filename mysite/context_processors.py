import datetime

from django.conf import settings

SETTINGS_TO_ADD = (
    'GOOGLE_ANALYTICS_ACCOUNT',
    'SOURCE_HINTS',
    'MEDIA_URL',
)

def add_settings(request):
    """Add some selected settings values to the context"""

    return {
        'settings': {
            k: getattr(settings, k) for k in SETTINGS_TO_ADD
        }
    }

def show_banner(request):
    """
    hacked in to display to FF banner
    """
    end_timestamp = 1425056400
    end_date = datetime.datetime.fromtimestamp(end_timestamp)
    if datetime.datetime.now() < end_date:
        delta = end_date - datetime.datetime.now()
        days = delta.days
        hours = delta.seconds/3600

        return {
            'ff_show_banner': True,
            'ff_days': days,
            'ff_hours': hours,
        }
