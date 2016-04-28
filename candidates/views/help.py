from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.views.generic import TemplateView

from elections.models import Election

class HelpApiView(TemplateView):
    template_name = 'candidates/api.html'

    def get_context_data(self, **kwargs):
        context = super(HelpApiView, self).get_context_data(**kwargs)

        context['grouped_elections'] = Election.group_and_order_elections()

        context['base_api_url'] = self.request.build_absolute_uri(
            reverse('api-root', kwargs={'version': 'v0.9'})
        )
        return context


class HelpAboutView(TemplateView):
    template_name = 'candidates/about.html'
