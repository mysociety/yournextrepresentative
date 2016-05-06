from django.db import models

from django_extensions.db.models import TimeStampedModel

from ..constants import REPORTED_RESULT_STATUSES

class BaseResultSetQuerySet(models.query.QuerySet):
    def confirmed(self):
        return self.filter(review_status='confirmed')

    def unconfirmed(self):
        return self.filter(review_status__in=['unconfirmed', ''])

    def rejected(self):
        return self.filter(review_status='rejected')


class BaseResultSetManager(models.Manager):
    def get_query_set(self):
        """ Use ActivatorQuerySet for all results """
        return BaseResultSetQuerySet(
            model=self.model, using=self._db)

    def get_queryset(self):
        """ Use ActivatorQuerySet for all results """
        return BaseResultSetQuerySet(
            model=self.model, using=self._db)

    def confirmed(self):
            return self.get_query_set().confirmed()

    def unconfirmed(self):
        return self.get_query_set().unconfirmed()

    def rejected(self):
        return self.get_query_set().rejected()


class BaseResultModel(TimeStampedModel):
    class Meta:
        abstract = True
        get_latest_by = "modified"

    source = models.TextField(null=True)

    objects = BaseResultSetManager()




class ResultStatusMixin(models.Model):
    class Meta:
        abstract = True

    is_final = models.BooleanField(default=False)
    final_source = models.TextField(null=True)

    review_status = models.CharField(blank=True, max_length=100,
        choices=REPORTED_RESULT_STATUSES)


    reviewed_by = models.ForeignKey(
        'auth.User',
        null=True,
    )
    review_source = models.TextField(null=True)
