from __future__ import unicode_literals

from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _

from ..models import LoggedAction
from popolo.models import Person


class ContributorsMixin(object):

    def get_leaderboards(self):
        result = []
        for title, since in [
            (_('All Time'), None),
            (_('In the last week'), timezone.now() - timedelta(days=7))
        ]:
            interesting_actions=LoggedAction.objects.exclude(
                action_type='set-candidate-not-elected'
            )
            if since:
                qs = interesting_actions.filter(created__gt=since)
            else:
                qs = interesting_actions
            qs = qs.exclude(user__isnull=True)
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
        ignored = ('set-candidate-not-elected', 'settings-edited')
        return LoggedAction.objects.exclude(
            action_type__in=ignored).order_by('-created')


class PersonMixin(object):

    @cached_property
    def person(self):
        return get_object_or_404(
            Person.objects.select_related('extra'),
            pk=self.kwargs['person_id'])

    # We include *args in the signature so this can be used by
    # SessionWizardView subclasses whose get_context_data has the
    # parameters (self, form, **kwargs) as opposed to the core Django
    # CBVs, which use (self, **kwargs)
    def get_context_data(self, *args, **kwargs):
        context = super(PersonMixin, self).get_context_data(*args, **kwargs)
        context['person'] = self.person
        return context
