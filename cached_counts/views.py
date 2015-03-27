import json

from django.shortcuts import render
from django.http import HttpResponse

from django.views.generic import ListView, TemplateView

from .models import CachedCount

class ReportsHomeView(TemplateView):
    template_name = "reports.html"

    def get_counts(self, context=None):
        if not context:
            context = {}
        for object_id in (
                'candidates_2015',
                'candidates_2010',
                'new_candidates',
                'standing_again',
                'standing_again_same_party',
                'standing_again_different_party',
        ):
            try:
                context[object_id] = CachedCount.objects.get(
                    object_id=object_id).count
            except CachedCount.DoesNotExist:
                pass
        if context.get('candidates_2010') and 'candidates_2015' in context:
            context['percent_of_2010'] = \
                (100 * float(context['candidates_2015'])) / \
                context['candidates_2010']
        return context

    def get_context_data(self, **kwargs):
        context = super(ReportsHomeView, self).get_context_data(**kwargs)
        context = self.get_counts(context)
        return context

    def get(self, *args, **kwargs):
        if self.request.GET.get('format') == "json":
            return HttpResponse(
                json.dumps(self.get_counts()),
                content_type="application/json"
            )
        return super(ReportsHomeView, self).get(*args, **kwargs)


class PartyCountsView(ListView):
    template_name = "party_counts.html"
    queryset = CachedCount.objects.filter(count_type='party')

class ConstituencyCountsView(ListView):
    template_name = "constituency_counts.html"
    queryset = CachedCount.objects.filter(count_type='constituency')
