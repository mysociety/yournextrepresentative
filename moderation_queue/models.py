import datetime

from django.contrib.auth.models import User
from django.db import models


PHOTO_REVIEWERS_GROUP_NAME = 'Photo Reviewers'


class QueuedImage(models.Model):

    APPROVED = 'approved'
    REJECTED = 'rejected'
    UNDECIDED = 'undecided'
    IGNORE = 'ignore'

    DECISION_CHOICES = (
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (UNDECIDED, 'Undecided'),
        (IGNORE, 'Ignore'),
    )

    PUBLIC_DOMAIN = 'public-domain'
    COPYRIGHT_ASSIGNED = 'copyright-assigned'
    PROFILE_PHOTO = 'profile-photo'
    OTHER = 'other'

    WHY_ALLOWED_CHOICES = (
        (PUBLIC_DOMAIN,
         "This photograph is free of any copyright restrictions"),
        (COPYRIGHT_ASSIGNED,
         "I own copyright of this photo and I assign the copyright " + \
         "to Democracy Club Limited in return for it being displayed " + \
         "on YourNextMP"),
        (PROFILE_PHOTO,
         "This is the candidate's public profile photo from social " + \
         "media (e.g. Twitter, Facebook) or their official campaign " + \
         "page"),
        (OTHER,
         "Other"),
    )

    why_allowed = models.CharField(
        max_length=64,
        choices=WHY_ALLOWED_CHOICES,
        default=OTHER,
    )
    justification_for_use = models.TextField(blank=True)
    decision = models.CharField(
        max_length=32,
        choices=DECISION_CHOICES,
        default=UNDECIDED
    )
    image = models.ImageField(
        upload_to='queued-images/%Y/%m/%d',
        max_length=512,
    )
    popit_person_id = models.CharField(max_length=256)
    user = models.ForeignKey(User, blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True, default=datetime.datetime.now)
    updated = models.DateTimeField(auto_now=True, default=datetime.datetime.now)

    def __unicode__(self):
        message = u'Image uploaded by {user} of candidate {popit_person_id}'
        return message.format(
            user=self.user,
            popit_person_id=self.popit_person_id
        )
