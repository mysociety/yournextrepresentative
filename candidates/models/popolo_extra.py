from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.db import models

from elections.models import Election, AreaType
from popolo.models import Person, Organization, Post, Membership, Area
from images.models import Image, HasImageMixin

"""Extensions to the base django-popolo classes for YourNextRepresentative

These are done via explicit one-to-one fields to avoid the performance
problems with multi-table inheritance; it's preferable to state when you
want a join or not.

  http://stackoverflow.com/q/23466577/223092

"""


class PersonExtra(HasImageMixin, models.Model):
    base = models.OneToOneField(Person, related_name='extra')

    # These two fields are added just for Burkina Faso - we should
    # have a better way of adding arbitrary fields which are only
    # needed for one site.
    cv = models.TextField(blank=True)
    program = models.TextField(blank=True)

    # This field stores JSON data with previous version information
    # (as it did in PopIt).
    versions = models.TextField(blank=True)

    images = generic.GenericRelation(Image)

    not_standing = models.ManyToManyField(
        Election, related_name='persons_not_standing'
    )

    def __unicode__(self):
        # WARNING: This will cause an extra query when getting the
        # repr() or unicode() of this object unless the base object
        # has been select_related.
        return self.base.name


class OrganizationExtra(models.Model):
    base = models.OneToOneField(Organization, related_name='extra')
    slug = models.CharField(max_length=256, blank=True)

    # For parties, which party register is it on:
    register = models.CharField(blank=True, max_length=512)

    images = generic.GenericRelation(Image)

    def __unicode__(self):
        # WARNING: This will cause an extra query when getting the
        # repr() or unicode() of this object unless the base object
        # has been select_related.
        return self.base.name


class PostExtra(HasImageMixin, models.Model):
    base = models.OneToOneField(Post, related_name='extra')
    slug = models.CharField(max_length=256, blank=True)

    candidates_locked = models.BooleanField(default=False)
    elections = models.ManyToManyField(Election, related_name='posts')
    group = models.CharField(max_length=1024, blank=True)
    party_set = models.ForeignKey('PartySet', blank=True, null=True)

    def __unicode__(self):
        # WARNING: This will cause an extra query when getting the
        # repr() or unicode() of this object unless the base object
        # has been select_related.
        return self.base.label


class MembershipExtra(models.Model):
    base = models.OneToOneField(Membership, related_name='extra')

    elected = models.NullBooleanField()
    party_list_position = models.IntegerField(null=True)
    election = models.ForeignKey(
        Election, blank=True, null=True, related_name='candidacies'
    )


class AreaExtra(models.Model):
    base = models.OneToOneField(Area, related_name='extra')

    type = models.ForeignKey(AreaType, blank=True, null=True, related_name='areas')

    def __unicode__(self):
        # WARNING: This will cause an extra query when getting the
        # repr() or unicode() of this object unless the base object
        # has been select_related.
        return self.base.name


class PartySet(models.Model):
    slug = models.CharField(max_length=256)
    name = models.CharField(max_length=1024)
    parties = models.ManyToManyField(Organization, related_name='party_sets')

    def __unicode__(self):
        return self.name

    def party_choices(self):
        result = list(self.parties.order_by('name').values_list('id', 'name'))
        result.insert(0, ('party:none', ''))
        return result


class ImageExtra(models.Model):
    base = models.OneToOneField(Image, related_name='extra')

    copyright = models.CharField(max_length=64, default='other', blank=True)
    uploading_user = models.ForeignKey(User, blank=True, null=True)
    user_notes = models.TextField(blank=True)
    md5sum = models.CharField(max_length=32, blank=True)
    user_copyright = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)
