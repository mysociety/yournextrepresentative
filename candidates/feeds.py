from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from django.utils.feedgenerator import Atom1Feed

from .models import LoggedAction

class RecentChangesFeed(Feed):
    title = "YourNextMP recent changes"
    description = "Changes to YNMP candidates"
    link = "/feeds/changes.xml"
    feed_type = Atom1Feed

    def items(self):
        return LoggedAction.objects.order_by('-updated')[:50]

    def item_title(self, item):
        return "{0} - {1}".format(
            item.popit_person_id,
            item.action_type
            )

    def item_description(self, item):
        description =  """
        {0}

        Updated at {1}
        """.format(
            item.source,
            str(item.updated),
        )

        return description

    def item_link(self, item):
        return reverse('person-view', args=[item.popit_person_id])
