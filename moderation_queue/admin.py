from __future__ import unicode_literals

from django.contrib import admin
from .models import QueuedImage

class QueuedImageAdmin(admin.ModelAdmin):
    list_display = ('user', 'person', 'created', 'decision')
    search_fields = ('user__username', 'person__id')
    exclude = ('person',)
    list_filter = ('decision',)
    ordering = ('-created',)

    def get_queryset(self, request):
        qs = super(QueuedImageAdmin, self).get_queryset(request)
        return qs.select_related('person', 'user')

admin.site.register(QueuedImage, QueuedImageAdmin)
