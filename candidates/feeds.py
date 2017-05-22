# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.contrib.sites.models import Site
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from django.utils.feedgenerator import Atom1Feed
from django.utils.translation import ugettext_lazy as _

from .models import LoggedAction

lock_re = re.compile(r'^(?:Unl|L)ocked\s*constituency (.*) \((\d+)\)$')


class ChangesMixin(object):
    def get_title(self, logged_action):
        if logged_action.person:
            return "{0} ({1}) - {2}".format(
                logged_action.person.name,
                logged_action.person_id,
                logged_action.action_type,
            )
        elif logged_action.post:
            return "{0} ({1}) - {2}".format(
                logged_action.post.label,
                logged_action.post.extra.slug,
                logged_action.action_type,
            )
        else:
            return logged_action.action_type

    def get_guid(self, logged_action):
        return self.id_format(logged_action.id)

    def get_updated(self, logged_action):
        # Note that we're using the created attribute rather than
        # updated, since any save() of the LoggedAction will cause
        # updated to be set to now, but the item won't really have
        # changed in a sense that means we'd want it to appear again
        # in an RSS feed.
        return logged_action.created

    def get_author(self, logged_action):
        if logged_action.user:
            return logged_action.user.username
        else:
            return "Automated change"


class RecentChangesFeed(ChangesMixin, Feed):
    site_name = Site.objects.get_current().name
    title = _("{site_name} recent changes").format(site_name=site_name)
    description = _("Changes to {site_name} candidates").format(site_name=site_name)
    link = "/feeds/changes.xml"
    feed_type = Atom1Feed
    id_format = 'changes:{0}'

    def items(self):
        return LoggedAction.objects.order_by('-updated')[:50]

    def item_title(self, item):
        return self.get_title(item)

    def item_description(self, item):
        updated = _("Updated at {0}").format(str(item.updated))
        description = "{0}\n\n{1}\n".format(item.source, updated)

        return description

    def item_guid(self, item):
        return self.id_format.format(item.id)

    def item_updateddate(self, item):
        return self.get_updated(item)

    def item_author_name(self, item):
        return self.get_author(item)

    def item_link(self, item):
        # As a hack for the moment, constituencies are just mentioned
        # in the source message:
        if item.person_id:
            return reverse('person-view', args=[item.person_id])
        else:
            return '/'


class NeedsReviewFeed(ChangesMixin, Feed):
    site_name = Site.objects.get_current().name
    title = _('{site_name} changes for review').format(site_name=site_name)
    link = '/feeds/needs-review.xml'
    feed_type = Atom1Feed
    id_format = 'needs-review:{0}'

    def items(self):
        # Consider changes in the last 5 days. We exclude any photo
        # related activity since that has its own reviewing system.
        return sorted(
            LoggedAction.objects \
                .exclude(action_type__startswith='photo-') \
                .in_recent_days(1) \
                .order_by('-created') \
                .needs_review().items(),
            key=lambda t: t[0].created,
            reverse=True)

    def item_title(self, item):
        return self.get_title(item[0])

    def item_guid(self, item):
        return self.id_format.format(item[0].id)

    def item_updateddate(self, item):
        return self.get_updated(item[0])

    def item_author_name(self, item):
        return self.get_author(item[0])

    def item_description(self, item):
        la = item[0]
        return '''
<p>{action_type} of {subject} by {user} with source: “ {source} ”;</p>
<ul>
{reasons_review_needed}
</ul></p>{diff}'''.strip().format(
            action_type=la.action_type,
            subject=la.subject_html,
            user=la.user.username,
            source=la.source,
            reasons_review_needed='\n'.join(
                '<li>{0}</li>'.format(i) for i in item[1]),
            timestamp=la.updated,
            diff=la.diff_html)

    def item_link(self, item):
        return item[0].subject_url
