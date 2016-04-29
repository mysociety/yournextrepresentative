from django.contrib import admin

from django.contrib import admin

from .models import (Council, CouncilElection, CouncilElectionResultSet,
                     PartyWithColour)


class ReadOnlyAdminMixIn(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if self.declared_fieldsets:
            return flatten_fieldsets(self.declared_fieldsets)
        else:
            readonly_fields = set(
                [field.name for field in self.opts.local_fields] +
                [field.name for field in self.opts.local_many_to_many]
            ) - set(getattr(self, 'exclude_from_read_only', []))

            return list(readonly_fields)


class CouncilAdmin(ReadOnlyAdminMixIn):
    modifiable = False
    search_fields = ['name']

    list_display = (
        '__str__',
    )


class CouncilElectionAdmin(admin.ModelAdmin):
    list_display = (
        'council', 'election',
    )

admin.site.register(Council, CouncilAdmin)
admin.site.register(PartyWithColour)
admin.site.register(CouncilElection, CouncilElectionAdmin)
admin.site.register(CouncilElectionResultSet)
