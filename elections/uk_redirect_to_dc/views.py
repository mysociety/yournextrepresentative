from __future__ import unicode_literals

from django.utils.six.moves.urllib_parse import urljoin
from django.views.generic import RedirectView


class RedirectToDCView(RedirectView):

    """Redirect all URLs to Democracy Club's new candidates site"""

    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        new_url = urljoin(
            'https://candidates.democracyclub.org.uk',
            self.request.get_full_path(),
        )
        return new_url
