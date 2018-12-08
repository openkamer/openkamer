from django.contrib import admin

from gift.models import Gift, PersonPosition


class GiftModel(admin.ModelAdmin):
    list_display = (
        'id',
        'person',
        'value_euro',
        'date',
        'description',
    )


class PersonPositionModel(admin.ModelAdmin):
    list_display = (
        'id',
        'person',
        'party',
        'parliament_member',
        'date',
    )


admin.site.register(Gift, GiftModel)
admin.site.register(PersonPosition, PersonPositionModel)
