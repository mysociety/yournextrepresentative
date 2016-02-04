from django.contrib import admin

from .models import Alert


@admin.register
class AlertAdmin(admin.ModelAdmin):
    list_display = \
        ['user', 'target', 'action', 'frequency', 'last_sent', 'enabled']
    list_filter = ('action', 'frequency', 'enabled')
