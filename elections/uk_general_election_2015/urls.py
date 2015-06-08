from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^$',
        views.ConstituencyPostcodeFinderView.as_view(),
        name='lookup-name'
    ),
    url(
        r'^lookup/name$',
        views.ConstituencyNameFinderView.as_view(),
        name='lookup-name'
    ),
    url(
        r'^lookup/postcode$',
        views.ConstituencyPostcodeFinderView.as_view(),
        name='lookup-postcode'
    ),
    # These should all be redirects to the new URL scheme:
    url(
        r'^constituencies(?P<list_filter>|/unlocked|/declared)$',
        views.ConstituenciesRedirect.as_view()
    ),
    url(
        r'^constituency/(?P<rest_of_path>.*)$',
        views.ConstituencyRedirect.as_view()
    ),
    # This regex is to catch the /party and /parties URLs:
    url(
        r'^part(?P<rest_of_path>.*)$',
        views.PartyRedirect.as_view()
    ),
    url(
        r'^candidacy(?P<rest_of_path>.*)$',
        views.CandidacyRedirect.as_view()
    ),
    url(
        r'^person/create/$',
        views.PersonCreateRedirect.as_view()
    ),
    url(
        r'^numbers/(?P<rest_of_path>constituencies|parties)$',
        views.CachedCountsRedirect.as_view()
    )
]
