from datetime import datetime
from random import randint
import sys

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.http import urlquote

from auth_helpers.views import user_in_group
from .version_data import create_version_id, get_current_timestamp
from ..cache import get_post_cached
from ..models import LoggedAction, TRUSTED_TO_LOCK_GROUP_NAME
from ..static_data import MapItData


class ContributorsMixin(object):

    def get_leaderboards(self):
        result = []
        for title, since in [
            ('All Time', None),
            ('In the last week', timezone.now() - timedelta(days=7))
        ]:
            if since:
                qs = LoggedAction.objects.filter(created__gt=since)
            else:
                qs = LoggedAction.objects.all()
            rows = qs.values('user'). \
                annotate(edit_count=Count('user')).order_by('-edit_count')[:25]
            for row in rows:
                row['username'] = User.objects.get(pk=row['user'])
            leaderboard = {
                'title': title,
                'rows': rows,
            }
            result.append(leaderboard)
        return result

    def get_recent_changes_queryset(self):
        return LoggedAction.objects.all().order_by('-created')


class CandidacyMixin(object):

    def get_area_from_post_id(self, post_id, mapit_url_key='id'):
        "Get a MapIt area ID from a candidate list organization's PopIt data"

        mapit_data = MapItData.constituencies_2010.get(post_id)
        if mapit_data is None:
            message = "Couldn't find the constituency with Post and MapIt Area ID: '{0}'"
            raise Exception(message.format(post_id))
        url_format = 'http://mapit.mysociety.org/area/{0}'
        return {
            'name': mapit_data['name'],
            'post_id': post_id,
            mapit_url_key: url_format.format(post_id),
        }

    def get_constituency_lock_from_person_data(self, person_data):
        """Return whether the constituency is locked and whether this user can edit"""

        standing_in = person_data.get('standing_in') or {}
        return self.get_constituency_lock(
            standing_in.get('2015', {}).get('post_id')
        )

    def get_constituency_lock(self, post_id):
        """Return whether the constituency is locked and whether this user can edit"""

        if not post_id:
            return False, True
        # Use the cached version because it'll be faster than going to
        # PopIt, even if it brings in embeds that we don't need:
        post_data = get_post_cached(self.api, post_id)['result']
        candidates_locked = bool(post_data.get('candidates_locked'))
        edits_allowed = (
            user_in_group(self.request.user, TRUSTED_TO_LOCK_GROUP_NAME) or
            not candidates_locked
        )
        return candidates_locked, edits_allowed
