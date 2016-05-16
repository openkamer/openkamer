from django.contrib import admin

from parliament.models import Parliament, ParliamentMember, PartyMember, PoliticalParty


class PoliticalPartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'founded', 'dissolved', 'wikidata_id', 'wikimedia_logo_url', 'wikipedia_url')


admin.site.register(Parliament)
admin.site.register(ParliamentMember)
admin.site.register(PartyMember)
admin.site.register(PoliticalParty, PoliticalPartyAdmin)