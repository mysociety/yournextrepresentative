from django.conf.urls import patterns, include, url

from .views import PartyCountsView, ConstituencyCountsView, ReportsHomeView

urlpatterns = patterns('',
    url(r'^$', ReportsHomeView.as_view(), name='reports_home'),
    url(r'parties$', PartyCountsView.as_view(), name='party_counts'),
    url(r'constituencies$', ConstituencyCountsView.as_view(), name='constituencies_counts'),
)