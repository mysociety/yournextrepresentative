from django.conf.urls import patterns, include, url

from .views import PartyCountsView, ConstituencyCountsView, ReportsHomeView

urlpatterns = patterns('',
    url(r'^$', ReportsHomeView.as_view(), name='reports_home'),
    url(r'^election/(?P<election>[-\w]+)/parties$', PartyCountsView.as_view(), name='parties_counts'),
    url(r'^election/(?P<election>[-\w]+)/posts$', ConstituencyCountsView.as_view(), name='posts_counts'),
)
