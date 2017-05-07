from django.conf.urls import url
from django.views.decorators.cache import cache_page
from django.views.decorators.clickjacking import xframe_options_exempt

from . import views


urlpatterns = [
    url(
        r'^$',
        views.ResultsHomeView.as_view(),
        name='results-home'
    ),


    # Control
    url(
        r'^councils$',
        views.CouncilsWithElections.as_view(),
        name='councils-with-elections'
    ),
    url(
        r'^(?P<election_id>.*\d\d\d\d-\d\d-\d\d)$',
        views.CouncilElectionView.as_view(),
        name='council-election-view'
    ),
    url(
        r'^(?P<election_id>[^/]+)/report$',
        views.ReportCouncilElectionView.as_view(),
        name='report-council-election-view'
    ),
    url(
        r'^latest_control$',
        views.LatestControlResults.as_view(),
        name='latest-control-view'
    ),
    url(
        r'^review_control/(?P<pk>[^/]+)$',
        views.ConfirmControl.as_view(),
        name='review-control-view'
    ),



    # Votes
    url(
        r'^posts/(?P<post_election_id>[\d]+)/$',
        views.PostResultsView.as_view(),
        name='post-results-view'
    ),

    url(
        r'^posts/(?P<post_election_id>[\d]+)/report$',
        views.PostReportVotesView.as_view(),
        name='report-post-votes-view'
    ),
    url(
        r'^posts/(?P<result_set_id>[\d]+)/review$',
        views.ReviewPostReportView.as_view(),
        name='review-votes-view'
    ),
    url(
        r'^posts$',
        views.LatestVoteResults.as_view(),
        name='latest-votes-view'
    ),

    url(
        r'^posts/(?P<post_slug>[^/]+)/$',
        views.PostResultsRedirectView.as_view(),
        name='post-result-redirect-view'
    ),



    # Map Views
    url(
        r'^map/data.json$',
        cache_page(60)(views.MapAreaView.as_view()),
        name='map-data-view'
    ),
    url(
        r'^map/embed$',
        xframe_options_exempt(cache_page(60)(views.MapEmbedView.as_view())),
        name='map-embed-view'
    ),
]

