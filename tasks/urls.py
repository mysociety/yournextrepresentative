from __future__ import unicode_literals

from django.conf.urls import url

from .views import IncompleteFieldView, TaskHomeView, CouldntFindFieldView

urlpatterns = [
    url(r'^$', TaskHomeView.as_view(), name='tasks_home'),
    url(
        r'couldnt_find_field/(?P<pk>\d+)',
        CouldntFindFieldView.as_view(),
        name='couldnt_find_field',
    ),
    url(
        r'(?P<field>[a-z_\-\.]+)/',
        IncompleteFieldView.as_view(),
        name='incomplete_view',
    ),
]
