import json

from django.http import HttpResponse
from django.views.generic import View

from candidates.models import PostExtra


class PostIDToPartySetView(View):

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        result = dict(
            PostExtra.objects.filter(elections__current=True) \
               .values_list('slug', 'party_set__slug')
        )
        return HttpResponse(
            json.dumps(result), content_type='application/json'
        )
