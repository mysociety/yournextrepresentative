from django.contrib import admin
from .models import Election

class ElectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'current')
    search_fields = ('name', 'slug')

admin.site.register(Election, ElectionAdmin)
