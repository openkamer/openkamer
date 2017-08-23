from django.contrib import admin

from stats.models import Plot
from stats.models import SeatsPerParty


class PlotAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'type',
        'datetime_updated',
    )


class SeatsPerPartyAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'date',
        'party',
        'seats',
        'datetime_updated',
    )

admin.site.register(Plot, PlotAdmin)
admin.site.register(SeatsPerParty, SeatsPerPartyAdmin)