from django.contrib import admin

from government.models import Government
from government.models import GovernmentMember
from government.models import GovernmentPosition
from government.models import Ministry


class GovernmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'wikidata_id'
    )


class GovernmentMemberAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'person',
        'position',
        'start_date',
        'end_date'
    )


class MinistryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'government'
    )


class GovernmentPositionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'position',
        'ministry'
    )


admin.site.register(Government, GovernmentAdmin)
admin.site.register(GovernmentMember, GovernmentMemberAdmin)
admin.site.register(GovernmentPosition, GovernmentPositionAdmin)
admin.site.register(Ministry, MinistryAdmin)