from django.shortcuts import render

from django.views.generic import ListView

from .models import CachedCount

class PartyCountsView(ListView):
    template_name = "party_counts.html"
    queryset = CachedCount.objects.filter(count_type='party')

class ConstituencyCountsView(ListView):
    template_name = "constituency_counts.html"
    queryset = CachedCount.objects.filter(count_type='constituency')
