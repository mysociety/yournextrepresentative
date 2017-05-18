from __future__ import unicode_literals

from django.conf.urls import url

from .views import (
    upload_photo, upload_photo_image, upload_photo_url,
    PhotoUploadSuccess, PhotoReviewList, PhotoReview,
    SuggestLockView, SuggestLockReviewListView,
    SOPNReviewRequiredView, PersonNameCleanupView
)

urlpatterns = [
    url(r'^photo/upload/(?P<person_id>\d+)$',
        upload_photo,
        name="photo-upload"),
    url(r'^photo/upload/image/(?P<person_id>\d+)$',
        upload_photo_image,
        name="photo-upload-image"),
    url(r'^photo/upload/url/(?P<person_id>\d+)$',
        upload_photo_url,
        name="photo-upload-url"),
    url(r'^photo/review$',
        PhotoReviewList.as_view(),
        name="photo-review-list"),
    url(r'^photo/review/(?P<queued_image_id>\d+)$',
        PhotoReview.as_view(),
        name="photo-review"),
    url(r'^photo/upload/(?P<person_id>\d+)/success$',
        PhotoUploadSuccess.as_view(),
        name="photo-upload-success"),
    url(r'^suggest-lock/(?P<election_id>.*)/$',
        SuggestLockView.as_view(),
        name="constituency-suggest-lock"),
    url(r'^suggest-lock/$',
        SuggestLockReviewListView.as_view(),
        name="suggestions-to-lock-review-list"),
    url(r'^sopn-review-required/$',
        SOPNReviewRequiredView.as_view(),
        name="sopn-review-required"),
    url(r'^person_name_cleanup/$',
        PersonNameCleanupView.as_view(),
        name="person_name_cleanup"),
]
