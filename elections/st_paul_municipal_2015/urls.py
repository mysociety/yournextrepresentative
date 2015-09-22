from django.conf import settings
from django.conf.urls import url

from . import views

post_ignored_slug_re = r'(?!record-winner$|retract-winner$|.*\.csv$).*'

urlpatterns = [
    url(
        r'^$',
        views.StPaulAddressFinder.as_view(),
        name='lookup-name'
    ),
    url(
        r'^areas/(?P<area_ids>.*?)$',
        views.StPaulAreasView.as_view(),
        name='st-paul-areas-view'
    ),
    url(
        r'^areas/(?P<type_and_area_ids>.*?)(?:/(?P<ignored_slug>.*))?$',
        views.StPaulAreasOfTypeView.as_view(),
        name='st-paul-areas-of-type-view'
    ),
    url(
        r'^election/(?P<election>.*)/post/(?P<post_id>.*)/$',
        views.StPaulDistrictDetailView.as_view(),
        name='district'
    ),
]
