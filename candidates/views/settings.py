from __future__ import unicode_literals

from django.conf import settings
from django.views.generic import FormView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from auth_helpers.views import GroupRequiredMixin
from ..forms import SettingsForm
from ..models import EDIT_SETTINGS_GROUP_NAME, LoggedAction, SiteSettings

from .version_data import get_client_ip


class SettingsView(GroupRequiredMixin, FormView):
    template_name = 'candidates/settings.html'
    form_class = SettingsForm
    required_group_name = EDIT_SETTINGS_GROUP_NAME

    def get_form_kwargs(self):
        kwargs = super(SettingsView, self).get_form_kwargs()
        # We're getting the current site settings in such a way as to
        # avoid using any of the convenience methods that return the
        # cached current UserSettings object, since is_valid may
        # subsequently update the object we set here.  (is_valid
        # doesn't save it to the database, but because the cached
        # object is updated, it still means that the object returned
        # by those conveninence method, including the
        # self.request.usersettings attribute set by the middleware,
        # may not be in sync with the database any more.
        kwargs['instance'], _ = SiteSettings.objects.get_or_create(
            site_id=settings.SITE_ID,
            defaults={'user': self.request.user}
        )
        return kwargs

    def form_valid(self, form):
        settings = SiteSettings.objects.get_current()
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
        # n.b. saving the settings object automatically clears the
        # cache of current UserSettings.
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
