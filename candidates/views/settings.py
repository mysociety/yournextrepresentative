from __future__ import unicode_literals

from django.views.generic import FormView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from auth_helpers.views import GroupRequiredMixin
from ..forms import SettingsForm
from ..models import EDIT_SETTINGS_GROUP_NAME


class SettingsView(GroupRequiredMixin, FormView):
    template_name = 'candidates/settings.html'
    form_class = SettingsForm
    required_group_name = EDIT_SETTINGS_GROUP_NAME

    def get_context_data(self, **kwargs):
        context = super(SettingsView, self).get_context_data(**kwargs)

        settings = self.request.usersettings
        context['form'] = SettingsForm(instance=settings)

        return context

    def form_valid(self, form):
        settings = self.request.usersettings
        for field in form.fields:
            setattr(settings, field, form[field].value())
        settings.user = self.request.user
        settings.save()

        return HttpResponseRedirect(reverse('settings'))
