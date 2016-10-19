from django.contrib import admin

from government.models import Government


class GovernmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'wikidata_id'
    )

admin.site.register(Government, GovernmentAdmin)