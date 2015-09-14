from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from candidates.views import AddressFinderView
from candidates.forms import AddressForm

from cached_counts.models import CachedCount

from pygeocoder import Geocoder, GeocoderError
import requests

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
            reverse('areas-view', kwargs=resolved_address)
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

    lat, lon = location_results[0].coordinates

    # TODO: This is where the p in p junk needs to happen
    # types_and_areas = ','.join(
    #     '{0}-{1}'.format(a[1]['type'],a[0]) for a in
    #     sorted_mapit_results
    # )
    # area_slugs = [slugify(a[1]['name']) for a in sorted_mapit_results]
    # ignored_slug = '-'.join(area_slugs)

    return {
        'type_and_area_ids': types_and_areas,
        'ignored_slug': ignored_slug,
    }
