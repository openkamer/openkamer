from django.contrib import admin

from parliament.models import Person


class PersonAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'fullname',
        'forename',
        'surname',
        'surname_prefix',
        'initials',
        'slug',
        'birthdate',
        'tk_id',
        'wikidata_id',
        'parlement_and_politiek_id',
        'datetime_updated',
    )


admin.site.register(Person, PersonAdmin)
