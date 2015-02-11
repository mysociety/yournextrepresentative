from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import TemplateView

from .mixins import ContributorsMixin

class RecentChangesView(ContributorsMixin, TemplateView):
    template_name = 'candidates/recent-changes.html'

    def get_context_data(self, **kwargs):
        context = super(RecentChangesView, self).get_context_data(**kwargs)
        actions = self.get_recent_changes_queryset()
        paginator = Paginator(actions, 50)
        page = self.request.GET.get('page')
        try:
            context['actions'] = paginator.page(page)
        except PageNotAnInteger:
            context['actions'] = paginator.page(1)
        except EmptyPage:
            context['actions'] = paginator.page(paginator.num_pages)
        return context

class LeaderboardView(ContributorsMixin, TemplateView):
    template_name = 'candidates/leaderboard.html'

    def get_context_data(self, **kwargs):
        context = super(LeaderboardView, self).get_context_data(**kwargs)
        context['leaderboards'] = self.get_leaderboards()
        return context
