import json

import requests

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import FormView, TemplateView

from .forms import PostcodeForm

class ConstituencyFinderView(FormView):
    template_name = 'candidates/finder.html'
    form_class = PostcodeForm

    def form_valid(self, form):
        postcode = form.cleaned_data['postcode']
        url = 'http://mapit.mysociety.org/postcode/' + postcode
        r = requests.get(url)
        mapit_result = r.json
        mapit_constituency_id = mapit_result['shortcuts']['WMC']
        mapit_constituency_data = mapit_result['areas'][str(mapit_constituency_id)]
        constituency_url = reverse(
            'constituency',
            kwargs={'constituency_name': mapit_constituency_data['name']}
        )
        return HttpResponseRedirect(constituency_url)


class ConstituencyDetailView(TemplateView):
    template_name = 'candidates/constituency.html'
