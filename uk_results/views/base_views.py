import json

from django.views.generic import TemplateView, View
from django.http import HttpResponse

from ..models import ElectionArea
from .base import BaseResultsViewMixin

class ResultsHomeView(BaseResultsViewMixin, TemplateView):
    template_name = "uk_results/home.html"


class MapAreaView(View):
    def get(self, request, *args, **kwargs):
        parent = None
        if request.GET.get('parent'):
            parent = ElectionArea.objects.get(area_gss=request.GET['parent'])
        data = {}
        for area in ElectionArea.objects.filter(parent=parent):
            data[area.area_gss] = json.loads(area.geo_json)

        return HttpResponse(
            json.dumps(data), content_type='application/json'
        )
