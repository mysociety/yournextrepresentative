from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone

from ..models import LoggedAction
from ..static_data import MapItData


class ContributorsMixin(object):

    def get_leaderboards(self):
        result = []
        for title, since in [
            ('All Time', None),
            ('In the last week', timezone.now() - timedelta(days=7))
        ]:
            interesting_actions=LoggedAction.objects.exclude(
                action_type='set-candidate-not-elected'
            )
            if since:
                qs = interesting_actions.filter(created__gt=since)
            else:
                qs = interesting_actions
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
        return LoggedAction.objects.exclude(action_type='set-candidate-not-elected').order_by('-created')
