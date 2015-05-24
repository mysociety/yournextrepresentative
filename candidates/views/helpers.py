from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from slugify import slugify

from ..models import get_constituency_name_from_mapit_id

def get_redirect_from_mapit_id(election, mapit_id):
    constituency_name = get_constituency_name_from_mapit_id(mapit_id)
    return HttpResponseRedirect(
        reverse(
            'constituency',
            kwargs={
                'election': election,
                'mapit_area_id': mapit_id,
                'ignored_slug': slugify(constituency_name),
            }
        )
    )
