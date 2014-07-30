from django.conf.urls import patterns, include, url

from django.contrib import admin

from candidates.views import ConstituencyFinderView

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', ConstituencyFinderView.as_view(), name='finder'),
    url(r'^admin/', include(admin.site.urls)),
)
