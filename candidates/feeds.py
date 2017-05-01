from __future__ import unicode_literals

import re

from django.contrib.sites.models import Site
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from django.utils.feedgenerator import Atom1Feed
from django.utils.html import escape
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from .models import LoggedAction

lock_re = re.compile(r'^(?:Unl|L)ocked\s*constituency (.*) \((\d+)\)$')


class RecentChangesFeed(Feed):
    site_name = Site.objects.get_current().name
    title = _("{site_name} recent changes").format(site_name=site_name)
    description = _("Changes to {site_name} candidates").format(site_name=site_name)
    link = "/feeds/changes.xml"
    feed_type = Atom1Feed

    def items(self):
        return LoggedAction.objects.order_by('-updated')[:50]

    def item_title(self, item):
        return "{0} - {1}".format(
            item.person_id,
            item.action_type
        )

    def item_description(self, item):
        updated = _("Updated at {0}").format(str(item.updated))
        description = "{0}\n\n{1}\n".format(item.source, updated)

        return description

    def item_link(self, item):
        # As a hack for the moment, constituencies are just mentioned
        # in the source message:
        if item.person_id:
            return reverse('person-view', args=[item.person_id])
        else:
            return '/'


class NeedsReviewFeed(Feed):
    site_name = Site.objects.get_current().name
    title = _('{site_name} changes for review').format(site_name=site_name)
    link = '/feeds/needs-review.xml'
    feed_type = Atom1Feed

    def items(self):
        # Consider changes in the last 5 days:
        return sorted(
            LoggedAction.objects.in_recent_days(5).needs_review().items(),
            key=lambda t: t[0].created,
            reverse=True)

    def item_title(self, item):
        if item[0].person:
            return "{0} ({1}) - {2}".format(
                item[0].person.name,
                item[0].person_id,
                item[0].action_type,
            )
        elif item[0].post:
            return "{0} ({1}) - {2}".format(
                item[0].post.label,
                item[0].post.extra.slug,
                item[0].action_type,
            )
        else:
            return item[0].action_type

    def item_description(self, item):
        la = item[0]
        unescaped = '''
<p>{action_type} of {subject} by {user} with source: &ldquo;{source}&rdquo;</p>
<ul>
{reasons_review_needed}
</ul>
<p>Updated at {timestamp}</p>'''.strip().format(
            action_type=la.action_type,
            subject=la.subject_html,
            user=la.user.username,
            source=la.source,
            reasons_review_needed='\n'.join(
                '<li>{0}</li>'.format(i) for i in item[1]),
            timestamp=la.updated)
        return escape(unescaped)

    def item_link(self, item):
        return item[0].subject_url
