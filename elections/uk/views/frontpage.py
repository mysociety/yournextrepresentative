from __future__ import unicode_literals

import random

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView

from candidates.views.mixins import ContributorsMixin
from candidates.models import PostExtra
from tasks.models import PersonTask


from elections.models import Election

from ..forms import PostcodeForm
from ..mapit import get_areas_from_postcode


class ConstituencyPostcodeFinderView(ContributorsMixin, FormView):
    template_name = 'candidates/finder.html'
    form_class = PostcodeForm

    @method_decorator(cache_control(max_age=(60 * 10)))
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(ConstituencyPostcodeFinderView, self).dispatch(*args, **kwargs)

    def process_postcode(self, postcode):
        types_and_areas = get_areas_from_postcode(postcode)
        if settings.AREAS_TO_ALWAYS_RETURN:
            types_and_areas += settings.AREAS_TO_ALWAYS_RETURN
        types_and_areas_joined = ','.join(sorted(
            '{0}--{1}'.format(*t) for t in types_and_areas
        ))
        return HttpResponseRedirect(
            reverse('areas-view', kwargs={
                'type_and_area_ids': types_and_areas_joined
            })
        )

    def get_form_kwargs(self):
        if self.request.method == 'GET' and 'q' in self.request.GET:
            return {
                'data': self.request.GET,
                'initial': self.get_initial(),
                'prefix': self.get_prefix(),
            }
        else:
            return super(ConstituencyPostcodeFinderView, self).get_form_kwargs()

    def get(self, request, *args, **kwargs):
        if 'q' in request.GET:
            # The treat it like a POST request; we've overridden
            # get_form_kwargs to make sure the GET parameters are used
            # for the form in this case.
            return self.post(request, *args, **kwargs)
        else:
            return super(ConstituencyPostcodeFinderView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        return self.process_postcode(form.cleaned_data['q'])


    def sopn_progress_by_election(self, election_slug=None, election_qs=None):
        context = {}
        pe_qs = None
        if election_slug:
            pe_qs = PostExtra.objects.filter(
                elections__slug__startswith=election_slug)
        if election_qs:
            pe_qs = PostExtra.objects.filter(
                elections__in=election_qs)
        if not pe_qs:
            return context

        context['posts_total'] = pe_qs.count()
        context['posts_locked'] = pe_qs.filter(candidates_locked=True).count()
        context['posts_locked_percent'] = round(
                float(context['posts_locked']) /
                float(context['posts_total'])
                * 100)

        context['posts_lock_suggested'] = pe_qs.exclude(
            suggestedpostlock=None).count()
        context['posts_locked_suggested_percent'] = round(
                float(context['posts_lock_suggested']) /
                float(context['posts_total'])
                * 100)

        context['sopns_imported'] = pe_qs.exclude(
            base__officialdocument=None).count()
        context['sopns_imported_percent'] = round(
                float(context['sopns_imported']) /
                float(context['posts_total'])
                * 100)

        return context


    def get_context_data(self, **kwargs):
        context = super(ConstituencyPostcodeFinderView, self).get_context_data(**kwargs)
        context['postcode_form'] = kwargs.get('form') or PostcodeForm()
        context['show_postcode_form'] = True
        context['show_name_form'] = False
        context['top_users'] = self.get_leaderboards()[1]['rows'][:8]
        context['recent_actions'] = self.get_recent_changes_queryset()[:5]
        context['election_data'] = Election.objects.current().by_date().last()
        context['hide_search_form'] = True

        from uk_results.models import CouncilElection
        context['council_total'] = CouncilElection.objects.all().count()
        context['council_confirmed'] = CouncilElection.objects.filter(
            confirmed=True).count()

        if context['council_total']:
            context['council_election_percent'] = round(
                float(context['council_confirmed']) /
                float(context['council_total'])
                * 100)
        else:
            context['council_election_percent'] = 0

        from candidates.models import PostExtra
        from uk_results.models import PostResult
        context['votes_total'] = PostExtra.objects.filter(
            postextraelection__election__slug__contains="local").count()
        context['votes_confirmed'] = PostResult.objects.filter(
            confirmed=True).count()

        if float(context['votes_confirmed']):
            context['votes_percent'] = round(
                float(context['votes_confirmed']) /
                float(context['votes_total'])
                * 100)
        else:
            context['votes_percent'] = 0

        # context['council_election_percent'] = council_confirmed / council_total * 100
        election_qs = Election.objects.filter(slug__in=[
            "local.aberdeen-city.2017-05-04",
            "local.aberdeenshire.2017-05-04",
            "local.angus.2017-05-04",
            "local.argyll-and-bute.2017-05-04",
            "local.clackmannanshire.2017-05-04",
            "local.eilean-siar.2017-05-04",
            "local.dumfries-and-galloway.2017-05-04",
            "local.dundee-city.2017-05-04",
            "local.east-ayrshire.2017-05-04",
            "local.east-dunbartonshire.2017-05-04",
            "local.east-lothian.2017-05-04",
            "local.east-renfrewshire.2017-05-04",
            "local.city-of-edinburgh.2017-05-04",
            "local.falkirk.2017-05-04",
            "local.fife.2017-05-04",
            "local.glasgow-city.2017-05-04",
            "local.highland.2017-05-04",
            "local.inverclyde.2017-05-04",
            "local.midlothian.2017-05-04",
            "local.moray.2017-05-04",
            "local.north-ayrshire.2017-05-04",
            "local.north-lanarkshire.2017-05-04",
            "local.orkney-islands.2017-05-04",
            "local.perth-and-kinross.2017-05-04",
            "local.renfrewshire.2017-05-04",
            "local.the-scottish-borders.2017-05-04",
            "local.shetland-islands.2017-05-04",
            "local.south-ayrshire.2017-05-04",
            "local.south-lanarkshire.2017-05-04",
            "local.stirling.2017-05-04",
            "local.west-dunbartonshire.2017-05-04",
            "local.west-lothian.2017-05-04",
        ])
        context['scotland_sopn_progress'] = self.sopn_progress_by_election(
            election_qs=election_qs)

        task_count = PersonTask.objects.unfinished_tasks().count()
        if task_count > 0:
            random_offset = random.randrange(min(50, task_count))
            context['person_task'] = PersonTask.objects.unfinished_tasks()[random_offset]

        return context
