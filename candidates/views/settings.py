from __future__ import unicode_literals

from django.views.generic import FormView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from auth_helpers.views import GroupRequiredMixin
from ..forms import SettingsForm
from ..models import EDIT_SETTINGS_GROUP_NAME, LoggedAction

from .version_data import get_client_ip


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
        note = ''
        for field in form.fields:
            if form.cleaned_data[field] != getattr(settings, field):
                note += _(
                    'Changed {field_name} from "{old_value}" to "{new_value}"'
                    ).format(
                        field_name=field,
                        old_value=getattr(settings, field),
                        new_value=form[field].value()
                ) + "\n"
            setattr(settings, field, form[field].value())
        settings.user = self.request.user
        settings.save()

        request = self.request

        if note != '':
            LoggedAction.objects.create(
                user=request.user,
                action_type='settings-edited',
                ip_address=get_client_ip(request),
                popit_person_new_version='',
                person=None,
                source='',
                note=note
            )
        return HttpResponseRedirect(reverse('settings'))
