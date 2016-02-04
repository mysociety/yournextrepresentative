from django.db import models
from django.contrib.auth.models import User

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Alert(models.Model):
    user = models.ForeignKey(User)

    target_content_type = models.ForeignKey(
        ContentType,
        related_name='alert_target',
        blank=True,
        null=True
    )
    target_object_id = models.CharField(max_length=255, blank=True, null=True)
    target = GenericForeignKey('target_content_type', 'target_object_id')

    action = models.CharField(
        max_length=100,
        choices=(
            ('created', 'Created'),
            ('updated', 'Updated'),
            ('deleted', 'Deleted'),
            ('image_update', 'Images'),
            ('all', 'All'),
        )
    )

    frequency = models.CharField(
        max_length=100,
        choices=(
            ('hourly', 'Hourly'),
            ('daily', 'Daily')
        )
    )
    last_sent = models.DateTimeField()
    enabled = models.BooleanField(default=True)
