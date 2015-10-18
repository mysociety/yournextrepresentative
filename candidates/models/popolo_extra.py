from django.db import models

from elections.models import Election
from popolo.models import Person, Organization, Post, Membership

"""Extensions to the base django-popolo classes for YourNextRepresentative

These are done via explicit one-to-one fields to avoid the performance
problems with multi-table inheritance; it's preferable to state when you
want a join or not.

  http://stackoverflow.com/q/23466577/223092

"""


class PersonExtra(models.Model):
    base = models.OneToOneField(Person, related_name='extra')
    # FIXME: have to add multiple images


class OrganizationExtra(models.Model):
    base = models.OneToOneField(Organization, related_name='extra')

    # For parties, which party register is it on:
    register = models.CharField(blank=True, max_length=512)
    # FIXME: have to add multiple images (e.g. for party logos)


class PostExtra(models.Model):
    base = models.OneToOneField(Post, related_name='extra')

    elections = models.ManyToManyField(Election, related_name='posts')


class MembershipExtra(models.Model):
    base = models.OneToOneField(Membership, related_name='extra')

    election = models.ForeignKey(
        Election, blank=True, null=True, related_name='candidacies'
    )
