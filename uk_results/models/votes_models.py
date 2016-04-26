from __future__ import unicode_literals

import datetime

from django.db import models

from .base import BaseResultModel


class ResultSet(BaseResultModel):
    post = models.ForeignKey(
        'popolo.Post',
        related_name='result_sets',
    )

    # num_turnout_calculated = models.IntegerField()
    num_turnout_reported = models.IntegerField()
    num_spoilt_ballots = models.IntegerField()

    user = models.ForeignKey(
        'auth.User',
        related_name='result_sets',
        null=True,
    )

    ip_address = models.GenericIPAddressField()

    def __str__(self):
        return u"pk=%d user=%r post=%r" % (
            self.pk,
            self.user,
            self.post,
        )


class CandidateResult(BaseResultModel):
    result_set = models.ForeignKey(
        'ResultSet',
        related_name='candidate_results',
    )

    person = models.ForeignKey(
        'popolo.Person',
        related_name='candidate_results',
    )

    num_ballots_reported = models.IntegerField()
    is_winner = models.BooleanField(default=False)


    class Meta:
        ordering = ('person',)
        unique_together = (
            ('result_set', 'person'),
        )

    def __unicode__(self):
        return u"pk=%d title=%r" % (
            self.pk,
            self.title,
        )
