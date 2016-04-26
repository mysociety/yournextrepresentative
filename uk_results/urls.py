from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^$',
        views.ResultsHomeView.as_view(),
        name='results-home'
    ),
    url(
        r'^councils$',
        views.CouncilsWithElections.as_view(),
        name='councils-with-elections'
    ),
    url(
        r'^(?P<pk>[\d]+)$',
        views.CouncilElectionView.as_view(),
        name='council-election-view'
    ),
    url(
        r'^(?P<council_election>[^/]+)/report$',
        views.ReportCouncilElectionView.as_view(),
        name='report-council-election-view'
    ),
    url(
        r'^latest_control$',
        views.LatestControlResults.as_view(),
        name='latest-control-view'
    ),
    url(
        r'^confirm_control/(?P<pk>[\d]+)$',
        views.ConfirmControl.as_view(),
        name='confirm-control-view'
    ),
]

