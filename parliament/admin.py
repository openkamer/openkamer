from django.contrib import admin

from parliament.models import Parliament, ParliamentMember, PartyMember, PoliticalParty


class PoliticalPartyAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'name_short',
        'founded',
        'dissolved',
        'slug',
        'wikidata_id',
        'wikimedia_logo_url',
        'wikipedia_url',
        'official_website_url',
    )


admin.site.register(Parliament)
admin.site.register(ParliamentMember)
admin.site.register(PartyMember)
admin.site.register(PoliticalParty, PoliticalPartyAdmin)