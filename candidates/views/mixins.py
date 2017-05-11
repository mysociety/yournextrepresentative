from __future__ import unicode_literals

from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Count, F
from django.utils import timezone
from django.utils.translation import ugettext as _

from ..models import LoggedAction


class ContributorsMixin(object):

    def get_leaderboards(self, all_time=True):
        result = []
        boards = [
            (_('In the last week'), timezone.now() - timedelta(days=7))
        ]
        if all_time:
            boards.insert(0, (_('All Time'), None))


        for title, since in boards:
            interesting_actions=LoggedAction.objects.exclude(
                action_type='set-candidate-not-elected'
            )

            if since:
                qs = interesting_actions.filter(created__gt=since)
            else:
                qs = interesting_actions

            rows = qs.annotate(
                    username=F('user__username')
                ).values('username').annotate(
                    edit_count=Count('user')
                ).order_by('-edit_count')



            leaderboard = {
                'title': title,
                'rows': rows[:25],
            }
            result.append(leaderboard)
        return result

    def get_recent_changes_queryset(self):
        return LoggedAction.objects.exclude(
            action_type='set-candidate-not-elected'
        ).select_related(
            'user', 'person', 'post', 'post__extra'
        ).order_by('-created')
