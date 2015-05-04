from django.conf.urls import patterns

from .feeds import ResultEventsFeed

urlpatterns = patterns('',
    (r'^all\.atom$', ResultEventsFeed()),
)
