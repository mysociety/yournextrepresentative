from django.conf import settings
from django.views.generic import TemplateView

from ..popit import PopItApiMixin, get_base_url

class HelpApiView(PopItApiMixin, TemplateView):
    template_name = 'candidates/api.html'

    def get_context_data(self, **kwargs):
        context = super(HelpApiView, self).get_context_data(**kwargs)

        context['csv_list'] = []
        for election, election_data in settings.ELECTIONS_CURRENT:
            context['csv_list'].append({'slug': election, 'name': election_data['name']})

        context['popit_url'] = get_base_url()
        return context

class HelpAboutView(TemplateView):
    template_name = 'candidates/about.html'
