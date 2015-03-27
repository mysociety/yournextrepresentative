import json

from django.shortcuts import render
from django.http import HttpResponse

from django.views.generic import ListView, TemplateView

from .models import CachedCount

class ReportsHomeView(TemplateView):
    template_name = "reports.html"

    def get_counts(self):
        count_keys = (
            'candidates_2015',
            'candidates_2010',
            'new_candidates',
            'standing_again',
            'standing_again_same_party',
            'standing_again_different_party',
        )
        counts = {
            d['object_id']: d['count']
            for d in CachedCount.objects.filter(object_id__in=count_keys). \
                values('object_id', 'count')
        }
        if counts.get('candidates_2010') and 'candidates_2015' in counts:
            counts['percent_of_2010'] = \
                (100 * float(counts['candidates_2015'])) / \
                counts['candidates_2010']
        return counts

    def get_context_data(self, **kwargs):
        context = super(ReportsHomeView, self).get_context_data(**kwargs)
        context.update(self.get_counts())
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
