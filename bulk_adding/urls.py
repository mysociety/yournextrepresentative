from django.conf.urls import url

from candidates import constants

from . import views

urlpatterns = [
    url(
        r'^{election}/{post}/$'.format(
            election=constants.ELECTION_ID_REGEX,
            post=constants.POST_ID_REGEX
        ),
        views.BulkAddView.as_view(),
        name='bulk_add'
    ),
    url(
        r'^{election}/{post}/review/$'.format(
            election=constants.ELECTION_ID_REGEX,
            post=constants.POST_ID_REGEX
        ),
        views.BulkAddReviewView.as_view(),
        name='bulk_add_review'
    ),
    url(r'^$',
        views.UnlockedWithDocumentsView.as_view(),
        name='unlocked_posts_with_documents'),

]
