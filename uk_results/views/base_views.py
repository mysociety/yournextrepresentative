import json

from django.views.generic import TemplateView, View
from django.http import HttpResponse
from django.db.models import Count

from elections.models import Election

from ..models import ElectionArea
from ..constants import RESULTS_DATE
from .base import BaseResultsViewMixin


class ResultsHomeView(BaseResultsViewMixin, TemplateView):
    template_name = "uk_results/home.html"

    def get_context_data(self, **kwargs):
        context = super(ResultsHomeView, self).get_context_data(**kwargs)
        from uk_results.models import CouncilElection


        ec_qs = CouncilElection.objects.filter(
            election__election_date=RESULTS_DATE)
        ec_qs = ec_qs.annotate(
            post_count=Count('election__postextraelection__postextra')
            ).filter(post_count__gt=4)

        context['council_total'] = ec_qs.count()
        context['council_confirmed'] = ec_qs.filter(
            confirmed=True).count()

        context['council_election_percent'] = round(
            float(context['council_confirmed']) /
            float(context['council_total'])
            * 100)


        from candidates.models import PostExtraElection
        from uk_results.models import PostElectionResult
        context['votes_total'] = PostExtraElection.objects.filter(
            election__slug__contains="local",
            election__election_date=RESULTS_DATE,

        ).count()

        context['votes_confirmed'] = PostElectionResult.objects.filter(
            confirmed=True,
            post_election__election__election_date=RESULTS_DATE
        ).count()

        if float(context['votes_confirmed']):
            context['votes_percent'] = round(
                float(context['votes_confirmed']) /
                float(context['votes_total'])
                * 100)
        else:
            context['votes_percent'] = 0



        return context

    def test_func(self, user):
        return True


class MapAreaView(View):
    def get(self, request, *args, **kwargs):
        filter_kwargs = {
            'parent': None,
        }

        if request.GET.get('parent'):
            filter_kwargs['parent'] = ElectionArea.objects.get(
                area_gss=request.GET['parent'])

        if request.GET.get('only'):
            filter_kwargs['election__slug'] = request.GET['only']

        elections = Election.objects.only('slug').annotate(
            post_count=Count('postextraelection')
        ).filter(
            post_count__gt=4,
            slug__startswith="local.",
            election_date=RESULTS_DATE
        ).values_list('pk', flat=True)

        qs = ElectionArea.objects.filter(**filter_kwargs)
        qs = qs.select_related('election', 'winning_party')
        qs = qs.filter(election_id__in=elections)

        data = {}
        for area in qs:
            if not area.geo_json:
                continue
            data[area.area_gss] = json.loads(area.geo_json)
            data[area.area_gss]['election_name'] = \
                "<a href='{}{}'>{}</a>".format(
                    "/uk_results/",
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


class MapEmbedView(TemplateView):
    template_name = "uk_results/map_embed.html"
