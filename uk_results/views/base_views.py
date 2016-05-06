import json

from django.views.generic import TemplateView, View
from django.http import HttpResponse

from ..models import ElectionArea
from .base import BaseResultsViewMixin

class ResultsHomeView(BaseResultsViewMixin, TemplateView):
    template_name = "uk_results/home.html"

    def test_func(self, user):
        return True


class MapAreaView(View):
    def get(self, request, *args, **kwargs):
        filter_kwargs = {'parent': None}

        if request.GET.get('parent'):
            filter_kwargs['parent'] = ElectionArea.objects.get(
                area_gss=request.GET['parent'])

        if request.GET.get('only'):
            filter_kwargs['election__slug'] = request.GET['only']

        data = {}

        for area in ElectionArea.objects.filter(**filter_kwargs):
            data[area.area_gss] = json.loads(area.geo_json)
            data[area.area_gss]['election_name'] = "<a href='{}{}'>{}</a>".format(
                "https://candidates.democracyclub.org.uk/uk_results/",
                area.election.slug,
                area.election.name,
            )
            if area.winning_party:
                data[area.area_gss]['hex'] = area.winning_party.hex_value
            if area.noc:
                data[area.area_gss]['hex'] = "#AAA"

        return HttpResponse(
            json.dumps(data), content_type='application/json'
        )
