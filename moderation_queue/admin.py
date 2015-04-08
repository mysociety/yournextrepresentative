from django.contrib import admin
from .models import QueuedImage

class QueuedImageAdmin(admin.ModelAdmin):
    list_display = ('user', 'popit_person_id', 'created', 'decision')
    search_fields = ('user__username', 'popit_person_id')
    ordering = ('-created',)

admin.site.register(QueuedImage, QueuedImageAdmin)
