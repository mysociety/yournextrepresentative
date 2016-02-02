from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^$',
        views.ConstituencySelectorView.as_view(),
        name='cons-frontpage',
    ),
]
