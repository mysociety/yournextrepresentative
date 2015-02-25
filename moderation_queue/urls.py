from django.conf.urls import patterns, url

from .views import upload_photo, PhotoUploadSuccess

urlpatterns = patterns('',
    url(r'^photo/upload/(?P<popit_person_id>\d+)$',
        upload_photo,
        name="photo-upload"),
    url(r'^photo/upload/(?P<popit_person_id>\d+)/success$',
        PhotoUploadSuccess.as_view(),
        name="photo-upload-success"),
)
