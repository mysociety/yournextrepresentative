from __future__ import unicode_literals

from django.db import models

from elections.models import Election
from candidates.models import PartySet

from .base import BaseResultModel, ConfirmedResultMixin


class Council(models.Model):
    council_id = models.CharField(primary_key=True, max_length=100)
    council_type = models.CharField(blank=True, max_length=10)
    mapit_id = models.CharField(blank=True, max_length=100)
    name = models.CharField(blank=True, max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(blank=True, max_length=100)
    website = models.URLField(blank=True)
    postcode = models.CharField(blank=True, null=True, max_length=100)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('council', (), {'pk': self.pk})


class CouncilElection(models.Model):
    council = models.OneToOneField(Council)
    election = models.OneToOneField(Election)
    party_set = models.ForeignKey(PartySet)
    # TODO: Past Control?

    @models.permalink
    def get_absolute_url(self):
        return ('council-election-view', (), {'pk': self.pk})



class CouncilElectionResultSet(BaseResultModel, ConfirmedResultMixin):
    council_election = models.ForeignKey(CouncilElection)
    controller = models.ForeignKey('popolo.Organization', null=True)