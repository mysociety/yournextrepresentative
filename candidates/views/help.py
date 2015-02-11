from django.views.generic import TemplateView

from ..popit import PopItApiMixin

class HelpApiView(PopItApiMixin, TemplateView):
    template_name = 'candidates/api.html'

    def get_context_data(self, **kwargs):
        context = super(HelpApiView, self).get_context_data(**kwargs)
        context['popit_url'] = self.get_base_url()
        return context

class HelpAboutView(TemplateView):
    template_name = 'candidates/about.html'
