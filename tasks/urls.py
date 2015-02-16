from django.conf.urls import patterns, include, url

from .views import IncompleteFieldView

urlpatterns = patterns('',
    url(r'(?P<field>[^/]+)/', IncompleteFieldView.as_view(), name='incomplete_view'),
)