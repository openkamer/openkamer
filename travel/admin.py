from django.contrib import admin

from travel.models import Travel, TravelPersonPosition


class TravelModel(admin.ModelAdmin):
    list_display = (
        'id',
        'person',
        'destination',
        'purpose',
        'paid_by',
        'date_begin',
        'date_end',
    )


class TravelPersonPositionModel(admin.ModelAdmin):
    list_display = (
        'id',
        'person',
        'party',
        'parliament_member',
        'date',
    )


admin.site.register(Travel, TravelModel)
admin.site.register(TravelPersonPosition, TravelPersonPositionModel)
