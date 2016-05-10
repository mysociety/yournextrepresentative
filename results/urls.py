from __future__ import unicode_literals

from django.conf.urls import url

from .feeds import (
    BasicResultEventsFeed,
    ResultEventsFeed,
)


urlpatterns = [
    url(r'^all\.atom$', ResultEventsFeed(), name='atom-results'),
    url(r'^all-basic\.atom$', BasicResultEventsFeed(), name='atom-results-basic'),
]
