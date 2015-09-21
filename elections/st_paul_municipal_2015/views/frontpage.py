from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.text import slugify

from candidates.views import AddressFinderView
from candidates.forms import AddressForm

from cached_counts.models import CachedCount

from pygeocoder import Geocoder, GeocoderError
import requests

from elections.st_paul_municipal_2015.settings import OCD_BOUNDARIES_URL


class StPaulAddressForm(AddressForm):

    def clean_address(self):
        address = self.cleaned_data['address']
        check_address(address)
        return address

class StPaulAddressFinder(AddressFinderView):

    form_class = StPaulAddressForm
    country = 'United States'

    def form_valid(self, form):
        form.cleaned_data['address']
        resolved_address = check_address(
            form.cleaned_data['address'],
            country=self.country,
        )
        return HttpResponseRedirect(
            reverse('st-paul-areas-view', kwargs=resolved_address)
        )

    def get_context_data(self, **kwargs):
        context = super(StPaulAddressFinder, self).get_context_data(**kwargs)
        context['needing_attention'] = \
            CachedCount.get_attention_needed_queryset()[:5]
        return context

def check_address(address_string, country=None):
    tidied_address = address_string.strip()

    if country is not None:
        tidied_address += ', ' + country

    try:
        location_results = Geocoder.geocode(tidied_address)
    except GeocoderError:
        message = _(u"Failed to find a location for '{0}'")
        raise ValidationError(message.format(tidied_address))

    coords = [str(p) for p in location_results[0].coordinates]

    boundaries = requests.get('{0}/boundaries'.format(OCD_BOUNDARIES_URL),
                              params={'contains': ','.join(coords)})

    areas = set()

    for area in boundaries.json()['objects']:
        division_id = area['external_id']
        if not 'precinct' in division_id and 'ward' in division_id:
            area_slug = slugify(area['name'])
            areas.add('{0};{1}'.format(area_slug.rsplit('-', 1), area_slug))
        else:
            areas.add('1', 'city-1')

    # TODO: This is where the p in p junk needs to happen
    # types_and_areas = ','.join(
    #     '{0}-{1}'.format(a[1]['type'],a[0]) for a in
    #     sorted_mapit_results
    # )
    # area_slugs = [slugify(a[1]['name']) for a in sorted_mapit_results]
    # ignored_slug = '-'.join(area_slugs)

    return {
        'area_ids': ','.join(areas),
    }
