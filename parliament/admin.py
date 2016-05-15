from django.contrib import admin

from parliament.models import Parliament, ParliamentMember, PartyMember, PoliticalParty


class PoliticalPartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'founded', 'dissolved', 'logo', 'wikidata_uri')


admin.site.register(Parliament)
admin.site.register(ParliamentMember)
admin.site.register(PartyMember)
admin.site.register(PoliticalParty, PoliticalPartyAdmin)