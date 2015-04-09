import os

from django.db import models

from django_extensions.db.models import TimeStampedModel

DOCUMENT_UPLOADERS_GROUP_NAME = "Document Uploaders"


def document_file_name(instance, filename):
    return os.path.join(
        "official_documents",
        instance.mapit_id,
        filename,
    )


class OfficialDocument(TimeStampedModel):
    NOMINATION_PAPER = 'Nomination paper'

    DOCUMENT_TYPES = (
        (NOMINATION_PAPER, NOMINATION_PAPER),
    )

    document_type = models.CharField(
        blank=False,
        choices=DOCUMENT_TYPES,
        max_length=100)
    uploaded_file = models.FileField(
        upload_to=document_file_name, max_length=800)
    mapit_id = models.CharField(blank=False, max_length=50)
    source_url = models.URLField(blank=True,
        help_text="The page that links to this document")

    def __unicode__(self):
        return u"{0} ({1})".format(
            self.mapit_id,
            self.source_url,
        )

    @models.permalink
    def get_absolute_url(self):
        return ('uploaded_document_view', (), {'pk': self.pk})
