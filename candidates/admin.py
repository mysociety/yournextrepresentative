from django.contrib import admin
from django.forms import ModelForm

from .models import LoggedAction
# Register your models here.

class LoggedActionAdminForm(ModelForm):
    pass

class LoggedActionAdmin(admin.ModelAdmin):
    form = LoggedActionAdminForm
    list_display = ['user', 'action_type', 'popit_person_new_version',
                    'popit_person_id', 'created', 'updated', 'source']
    ordering = ('-created',)

admin.site.register(LoggedAction, LoggedActionAdmin)
