from django.conf.urls import patterns, include, url

from django.contrib import admin

from candidates.views import (ConstituencyFinderView,
    ConstituencyDetailView, CandidacyView)

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', ConstituencyFinderView.as_view(), name='finder'),
    url(r'^constituency/(?P<constituency_name>.*)$',
        ConstituencyDetailView.as_view(),
        name='constituency'),
    url(r'^candidacy$',
        CandidacyView.as_view(),
        name='candidacy'),
    url(r'^admin/', include(admin.site.urls)),
)
