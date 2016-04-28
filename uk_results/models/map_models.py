from __future__ import unicode_literals

from django.db import models


class ElectionArea(models.Model):
    area_gss = models.CharField(max_length=100)
    election = models.ForeignKey('elections.Election')
    parent = models.ForeignKey('self', null=True)
    area_name = models.CharField(blank=True, max_length=255)
    geo_json = models.TextField(blank=True)
