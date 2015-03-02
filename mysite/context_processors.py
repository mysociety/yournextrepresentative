from datetime import date
from django.conf import settings
from candidates.models import election_date_2015

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


def election_date(request):
    """Add knowledge of the election date to the context"""

    return {
        'DATE_ELECTION': election_date_2015,
        'DATE_TODAY': date.today(),
    }
