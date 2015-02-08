from django.views.generic import FormView

from .mixins import ContributorsMixin

from .helpers import get_redirect_from_mapit_id
from ..forms import (PostcodeForm, ConstituencyForm)
from ..mapit import get_wmc_from_postcode


class ConstituencyPostcodeFinderView(ContributorsMixin, FormView):
    template_name = 'candidates/finder.html'
    form_class = PostcodeForm

    def form_valid(self, form):
        wmc = get_wmc_from_postcode(form.cleaned_data['postcode'])
        return get_redirect_from_mapit_id(wmc)

    def get_context_data(self, **kwargs):
        context = super(ConstituencyPostcodeFinderView, self).get_context_data(**kwargs)
        context['postcode_form'] = kwargs.get('form') or PostcodeForm()
        context['constituency_form'] = ConstituencyForm()
        context['show_postcode_form'] = True
        context['show_name_form'] = False
        context['top_users'] = self.get_leaderboards()[1]['rows'][:8]
        context['recent_actions'] = self.get_recent_changes_queryset()[:5]
        return context


class ConstituencyNameFinderView(ContributorsMixin, FormView):
    template_name = 'candidates/finder.html'
    form_class = ConstituencyForm

    def form_valid(self, form):
        constituency_id = form.cleaned_data['constituency']
        return get_redirect_from_mapit_id(constituency_id)

    def get_context_data(self, **kwargs):
        context = super(ConstituencyNameFinderView, self).get_context_data(**kwargs)
        context['postcode_form'] = PostcodeForm()
        context['constituency_form'] = kwargs.get('form') or ConstituencyForm()
        context['show_postcode_form'] = False
        context['show_name_form'] = True
        context['top_users'] = self.get_leaderboards()[1]['rows'][:8]
        context['recent_actions'] = self.get_recent_changes_queryset()[:5]
        return context
