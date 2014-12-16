from django.shortcuts import render

from django.views.generic import ListView, TemplateView

from .models import CachedCount

class ReportsHomeView(TemplateView):
    template_name = "reports.html"

    def get_context_data(self, **kwargs):
        context = super(ReportsHomeView, self).get_context_data(**kwargs)
        try:
            context['candidates_2015'] = CachedCount.objects.get(
                object_id='candidates_2015').count
            context['percent_of_2010'] = 100 * float(
                context['candidates_2015'])/float(4152)
        except CachedCount.DoesNotExist:
            pass
        try:
            context['new_candidates'] = CachedCount.objects.get(
                object_id='new_candidates').count
        except CachedCount.DoesNotExist:
            pass
        try:
            context['standing_again'] = CachedCount.objects.get(
                object_id='standing_again').count
        except CachedCount.DoesNotExist:
            pass
        return context

class PartyCountsView(ListView):
    template_name = "party_counts.html"
    queryset = CachedCount.objects.filter(count_type='party')

class ConstituencyCountsView(ListView):
    template_name = "constituency_counts.html"
    queryset = CachedCount.objects.filter(count_type='constituency')
