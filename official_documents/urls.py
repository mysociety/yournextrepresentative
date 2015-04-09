from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'^upload/(?P<mapit_id>\d+)/$',
        views.CreateDocumentView.as_view(),
        name='upload_document_view'),
    url(r'^(?P<pk>\d+)/$',
        views.DocumentView.as_view(),
        name='uploaded_document_view'),
)
