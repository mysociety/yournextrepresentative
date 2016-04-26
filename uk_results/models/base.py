from django.db import models

from django_extensions.db.models import TimeStampedModel


class BaseResultModel(TimeStampedModel):
    class Meta:
        abstract = True

    source = models.TextField(null=True)


class ConfirmedResultMixin(models.Model):
    class Meta:
        abstract = True

    is_final = models.BooleanField(default=False)
    final_source = models.TextField(null=True)

    confirmed_by = models.ForeignKey(
        'auth.User',
        null=True,
    )
    confirm_source = models.TextField(null=True)
