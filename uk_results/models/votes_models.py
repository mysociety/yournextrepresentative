from __future__ import unicode_literals

from django.db import models
from django.db import transaction

from .base import BaseResultModel, ResultStatusMixin


class PostElectionResultManager(models.Manager):
    def confirmed(self):
        qs = self.filter(confirmed=True)
        if qs.exists():
            return qs.latest()
        else:
            return False



class PostElectionResult(models.Model):
    post_election = models.ForeignKey('candidates.PostExtraElection')
    confirmed = models.BooleanField(default=True)
    confirmed_resultset = models.OneToOneField(
        'ResultSet', null=True)

    objects = PostElectionResultManager()

    class Meta:
        get_latest_by = 'confirmed_resultset__created'

    @models.permalink
    def get_absolute_url(self):
        return ('post-results-view', (), {
            'post_election_id': self.post_election.pk})


class ResultSet(BaseResultModel, ResultStatusMixin):
    post_election_result = models.ForeignKey(
        PostElectionResult,
        related_name='result_sets',
    )

    # num_turnout_calculated = models.IntegerField()
    num_turnout_reported = models.IntegerField(null=True)
    num_spoilt_ballots = models.IntegerField(null=True)

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
            self.post_election_result,
        )

    def save(self, *args, **kwargs):
        super(ResultSet, self).save(*args, **kwargs)
        if self.review_status == "confirmed":
            self.post_election_result.confirmed = True
            self.post_election_result.confirmed_resultset = self
            if not self.review_source:
                self.review_source = self.source
            self.post_election_result.save()



class CandidateResult(BaseResultModel):
    result_set = models.ForeignKey(
        'ResultSet',
        related_name='candidate_results',
    )

    membership = models.ForeignKey(
        'popolo.Membership',
        related_name='result',
    )

    num_ballots_reported = models.IntegerField()
    is_winner = models.BooleanField(default=False)


    class Meta:
        ordering = ('-num_ballots_reported',)
        unique_together = (
            ('result_set', 'membership'),
        )

    def __unicode__(self):
        return u"{} ({} votes)".format(
            self.membership.person,
            self.num_ballots_reported
        )
