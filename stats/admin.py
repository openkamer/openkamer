from django.contrib import admin

from stats.models import Plot


class PlotAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'type',
        'datetime_updated',
    )

admin.site.register(Plot, PlotAdmin)