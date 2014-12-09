from django.conf.urls import patterns, include, url

from .views import PartyCountsView, ConstituencyCountsView

urlpatterns = patterns('',
    url(r'parties$', PartyCountsView.as_view(), name='party_counts'),
    url(r'constituencies$', ConstituencyCountsView.as_view(), name='constituencies_counts'),
)