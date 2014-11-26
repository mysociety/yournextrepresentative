from django.contrib import admin

from django.core.urlresolvers import reverse
from django.forms import ModelForm

from .models import LoggedAction
# Register your models here.

class LoggedActionAdminForm(ModelForm):
    pass

class LoggedActionAdmin(admin.ModelAdmin):
    form = LoggedActionAdminForm
    list_display = ['user', 'action_type', 'popit_person_new_version',
                    'popit_person_link', 'created', 'updated', 'source']
    ordering = ('-created',)

    def popit_person_link(self, o):
        url = reverse('person-view', kwargs={'person_id': o.popit_person_id})
        return '<a href="{0}">{1}</a>'.format(
            url,
            o.popit_person_id,
        )
    popit_person_link.allow_tags = True

admin.site.register(LoggedAction, LoggedActionAdmin)
