from __future__ import unicode_literals

import json
import requests
from collections import defaultdict

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.utils.six.moves.urllib_parse import urljoin
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, FormView

from candidates.models.address import check_address
from elections.models import Election, AreaType
from candidates import mapit

from .mixins import ContributorsMixin

from ..forms import AddressForm


class GeoLocatorView(View):
    def get(self, request, **kwargs):
        latitude = kwargs['latitude']
        longitude = kwargs['longitude']

        generation_with_types = defaultdict(list)
        for t in AreaType.objects.filter(election__current=True) \
                .values_list('election__area_generation', 'name'):
            generation_with_types[t[0]].append(t[1])

        mapit_base_url = urljoin(settings.MAPIT_BASE_URL,
                                 'point/4326/{lon},{lat}'.format(
                                     lon=longitude,
                                     lat=latitude,
                                 ))

        mapit_json = []
        for generation, types in generation_with_types.items():
            lookup_url = mapit_base_url + '?type=' \
                + ','.join(sorted(types))
            lookup_url += '&generation={0}'.format(generation)
            mapit_result = requests.get(lookup_url)
            mapit_result = mapit_result.json()
            if 'error' in mapit_result:
                message = _("The area lookup returned an error: '{0}'") \
                    .format(mapit_result['error'])
                return HttpResponse(
                    json.dumps({'error': message}),
                    content_type='application/json',
                )
            mapit_json += mapit_result.items()

        if len(mapit_json) == 0:
            message = _("Your location does not seem to be covered by this site")
            return HttpResponse(
                json.dumps({'error': message}),
                content_type='application/json',
            )

        ids_and_areas = [
            "{0}-{1}".format(
                area[1]['type'],
                mapit.format_code_from_area(area[1]))
            for area in mapit_json
        ]

        url = reverse('areas-view', kwargs={
            'type_and_area_ids': ','.join(sorted(ids_and_areas))
        })

        return HttpResponse(
            json.dumps({'url': url}),
            content_type='application/json',
        )



class AddressFinderView(ContributorsMixin, FormView):
    template_name = 'candidates/frontpage.html'
    form_class = AddressForm
    country = None

    @method_decorator(cache_control(max_age=(60 * 10)))
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(AddressFinderView, self).dispatch(*args, **kwargs)

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.country, **self.get_form_kwargs())

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
        context = super(AddressFinderView, self).get_context_data(**kwargs)
        context['top_users'] = self.get_leaderboards()[1]['rows'][:8]
        context['recent_actions'] = self.get_recent_changes_queryset()[:5]
        context['election_data'] = Election.objects.current().by_date().last()
        return context
