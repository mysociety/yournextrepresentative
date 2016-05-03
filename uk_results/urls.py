from django.conf.urls import url

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
        r'^posts/(?P<post_id>[^/]+)/$',
        views.PostResultsView.as_view(),
        name='post-results-view'
    ),

    url(
        r'^posts/(?P<post_id>[^/]+)/report$',
        views.PostReportVotesView.as_view(),
        name='report-post-votes-view'
    ),
    url(
        r'^posts/(?P<pk>[^/]+)/review$',
        views.ReviewPostReportView.as_view(),
        name='review-votes-view'
    ),
    url(
        r'^posts$',
        views.LatestVoteResults.as_view(),
        name='latest-votes-view'
    ),



    # Map Views
    url(
        r'^map/data.json$',
        views.MapAreaView.as_view(),
        name='map-data-view'
    ),
]

