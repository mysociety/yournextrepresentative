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
