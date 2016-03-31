from __future__ import unicode_literals

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView

from candidates.views.mixins import ContributorsMixin

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
            '{0}-{1}'.format(*t) for t in types_and_areas
        ))
        return HttpResponseRedirect(
            reverse('areas-view', kwargs={
                'type_and_area_ids': types_and_areas_joined
            })
        )

    def get(self, request, *args, **kwargs):
        if 'postcode' in request.GET:
            return self.process_postcode(request.GET['postcode'])
        else:
            return super(ConstituencyPostcodeFinderView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        return self.process_postcode(form.cleaned_data['postcode'])

    def get_context_data(self, **kwargs):
        context = super(ConstituencyPostcodeFinderView, self).get_context_data(**kwargs)
        context['postcode_form'] = kwargs.get('form') or PostcodeForm()
        context['show_postcode_form'] = True
        context['show_name_form'] = False
        context['top_users'] = self.get_leaderboards()[1]['rows'][:8]
        context['recent_actions'] = self.get_recent_changes_queryset()[:5]
        context['election_data'] = Election.objects.current().by_date().last()
        context['hide_search_form'] = True
        return context
