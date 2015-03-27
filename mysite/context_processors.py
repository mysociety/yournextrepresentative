from datetime import date
from django.conf import settings
from auth_helpers.views import user_in_group
from candidates.models import election_date_2015, TRUSTED_TO_MERGE_GROUP_NAME
from moderation_queue.models import PHOTO_REVIEWERS_GROUP_NAME

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


def add_group_permissions(request):
    """Add user_can_merge and user_can_review_photos"""

    return {
        context_variable: user_in_group(request.user, group_name)
        for context_variable, group_name in (
            ('user_can_merge', TRUSTED_TO_MERGE_GROUP_NAME),
            ('user_can_review_photos', PHOTO_REVIEWERS_GROUP_NAME),
        )
    }
