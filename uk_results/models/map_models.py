from __future__ import unicode_literals

from django.db import models


class ElectionArea(models.Model):
    area_gss = models.CharField(max_length=100)
    election = models.ForeignKey('elections.Election')
    parent = models.ForeignKey('self', null=True)
    area_name = models.CharField(blank=True, max_length=255)
    geo_json = models.TextField(blank=True)
    winning_party = models.ForeignKey('PartyWithColour', null=True)
    noc = models.BooleanField(default=False)


class PartyWithColour(models.Model):
    hex_value = models.CharField(blank=True, max_length=100)
    party = models.OneToOneField('popolo.Organization', primary_key=True)

    def __str__(self):
        return u"{} ({})".format(
            self.party,
            self.hex_value,
        )
