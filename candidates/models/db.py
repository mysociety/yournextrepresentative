from __future__ import unicode_literals

from collections import defaultdict
from datetime import datetime, timedelta
from functools import reduce

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.utils.html import escape
from django.utils.six import text_type

from slugify import slugify

from popolo.models import Person, Post

from .needs_review import needs_review_fns


def merge_dicts_with_list_values(dict_a, dict_b):
    return {
        k: dict_a.get(k, []) + dict_b.get(k, [])
        for k in set(dict_a.keys()) | set(dict_b.keys())
    }


class LoggedActionQuerySet(models.QuerySet):

    def in_recent_days(self, days=5):
        return self.filter(
            created__gte=(datetime.now() - timedelta(days=days)))

    def needs_review(self):
        '''Return a dict of LoggedAction -> list of reasons should be reviewed'''
        return reduce(
            merge_dicts_with_list_values,
            [f(self) for f in needs_review_fns],
            {}
        )


class LoggedAction(models.Model):
    '''A model for logging the actions of users on the site

    We record the changes that have been made to a person in PopIt in
    that person's 'versions' field, but is not much help for queries
    like "what has John Q User been doing on the site?". The
    LoggedAction model makes that kind of query easy, however, and
    should be helpful in tracking down both bugs and the actions of
    malicious users.'''

    user = models.ForeignKey(User, blank=True, null=True)
    person = models.ForeignKey(Person, blank=True, null=True)
    action_type = models.CharField(max_length=64)
    popit_person_new_version = models.CharField(max_length=32)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True)
    ip_address = models.CharField(max_length=50, blank=True, null=True)
    source = models.TextField()
    post = models.ForeignKey(Post, blank=True, null=True)

    objects = LoggedActionQuerySet.as_manager()

    def __repr__(self):
        fmt = str("<LoggedAction username='{username}' action_type='{action_type}'>")
        return fmt.format(username=self.user.username, action_type=self.action_type)

    @property
    def post_election_guess(self):
        """
        FIXME: Note that this won't always be correct because
        LoggedAction objects only reference Post at the moment,
        rather than a Post and an Election (or a PostExtraElection).
        """
        from candidates.models import PostExtraElection
        if self.post:
            election = self.post.extra.elections.order_by('-current').first()
            return PostExtraElection.objects.get(
                election=election,
                postextra=self.post.extra
            )

    @property
    def subject_url(self):
        pee = self.post_election_guess
        if pee:
            return reverse('constituency', kwargs={
                'election': pee.election.slug,
                'post_id': pee.postextra.slug,
                'ignored_slug': slugify(pee.postextra.short_label),
            })
        elif self.person:
            return reverse('person-view', kwargs={'person_id': self.person.id})
        return '/'

    @property
    def subject_html(self):
        pee = self.post_election_guess
        if pee:
            return '<a href="{url}">{text} ({post_slug})</a>'.format(
                url=self.subject_url,
                text=pee.postextra.short_label,
                post_slug=pee.postextra.slug,
            )
        elif self.person:
            return '<a href="{url}">{text} ({person_id})</a>'.format(
                url=self.subject_url,
                text=self.person.name,
                person_id=self.person.id)
        return ''

    @property
    def diff_html(self):
        from candidates.models import VersionNotFound
        if not self.person:
            return ''
        try:
            return self.person.extra.diff_for_version(
                self.popit_person_new_version, inline_style=True)
        except VersionNotFound as e:
            return '<p>{0}</p>'.format(escape(text_type(e)))


class PersonRedirect(models.Model):
    '''This represents a redirection from one person ID to another

    This is typically used to redirect from the person that is deleted
    after two people are merged'''
    old_person_id = models.IntegerField()
    new_person_id = models.IntegerField()

    @classmethod
    def all_redirects_dict(cls):
        new_to_sorted_old = defaultdict(list)
        for old, new in cls.objects.values_list(
                'old_person_id', 'new_person_id'):
            new_to_sorted_old[new].append(old)
        for v in new_to_sorted_old.values():
            v.sort()
        return new_to_sorted_old


class UserTermsAgreement(models.Model):
    user = models.OneToOneField(User, related_name='terms_agreement')
    assigned_to_dc = models.BooleanField(default=False)


def create_user_terms_agreement(sender, instance, created, **kwargs):
    if created:
        UserTermsAgreement.objects.create(user=instance)

post_save.connect(create_user_terms_agreement, sender=User)
