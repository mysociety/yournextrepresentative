from __future__ import unicode_literals

from django.conf.urls import url

from .views import (
    PartyCountsView, ConstituencyCountsView, ReportsHomeView, AttentionNeededView
)

urlpatterns = [
    url(r'^$', ReportsHomeView.as_view(), name='reports_home'),
    url(r'^attention-needed$', AttentionNeededView.as_view(), name='attention_needed'),
    url(r'^election/(?P<election>[-\w\.0-9]+)/parties$', PartyCountsView.as_view(), name='parties_counts'),
    url(r'^election/(?P<election>[-\w\.0-9]+)/posts$', ConstituencyCountsView.as_view(), name='posts_counts'),
]
