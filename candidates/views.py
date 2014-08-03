import json

import requests

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.http import urlquote
from django.views.generic import FormView, TemplateView

from .forms import PostcodeForm

class ConstituencyFinderView(FormView):
    template_name = 'candidates/finder.html'
    form_class = PostcodeForm

    def form_valid(self, form):
        postcode = form.cleaned_data['postcode']
        url = 'http://mapit.mysociety.org/postcode/' + postcode
        r = requests.get(url)
        if r.status_code == 200:
            mapit_result = r.json
            mapit_constituency_id = mapit_result['shortcuts']['WMC']
            mapit_constituency_data = mapit_result['areas'][str(mapit_constituency_id)]
            constituency_url = reverse(
                'constituency',
                kwargs={'constituency_name': mapit_constituency_data['name']}
            )
            return HttpResponseRedirect(constituency_url)
        else:
            error_url = reverse('finder')
            error_url += '?bad_postcode=' + urlquote(postcode)
            return HttpResponseRedirect(error_url)

    def get_context_data(self, **kwargs):
        context = super(ConstituencyFinderView, self).get_context_data(**kwargs)
        bad_postcode = self.request.GET.get('bad_postcode')
        if bad_postcode:
            context['bad_postcode'] = bad_postcode
        return context

class ConstituencyDetailView(TemplateView):
    template_name = 'candidates/constituency.html'
