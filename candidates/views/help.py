from __future__ import unicode_literals

from os.path import exists, join

from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView

from elections.models import Election

class HelpApiView(TemplateView):
    template_name = 'candidates/api.html'

    def get_context_data(self, **kwargs):
        context = super(HelpApiView, self).get_context_data(**kwargs)

        context['grouped_elections'] = Election.group_and_order_elections()
        context['help_results_url'] = reverse('help-results')

        context['base_api_url'] = self.request.build_absolute_uri(
            reverse('api-root', kwargs={'version': 'v0.9'})
        )
        return context


class HelpAboutView(TemplateView):
    template_name = 'candidates/about.html'


class HelpResultsView(TemplateView):
    template_name = 'candidates/results.html'

    def results_file_exists(self, election_slug):
        if election_slug is None:
            suffix = 'all'
        else:
            suffix = election_slug
        expected_file_location = join(
            settings.MEDIA_ROOT,
            'candidates-elected-{0}.csv'.format(suffix),
        )
        return exists(expected_file_location)

    def get_context_data(self, **kwargs):
        context = super(HelpResultsView, self).get_context_data(**kwargs)

        context['all_results_exists'] = self.results_file_exists(None)

        context['grouped_elections'] = Election.group_and_order_elections()
        for era_data in context['grouped_elections']:
            for date, elections in era_data['dates'].items():
                for role_data in elections:
                    for election_dict in role_data['elections']:
                        election = election_dict['election']
                        election_dict['results_file_exists'] = \
                            self.results_file_exists(election.slug)

        return context
