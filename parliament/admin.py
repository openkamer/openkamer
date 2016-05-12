from django.contrib import admin

from .models import Person, Parliament, ParliamentMember, PartyMember, PoliticalParty

admin.site.register(Person)
admin.site.register(Parliament)
admin.site.register(ParliamentMember)
admin.site.register(PartyMember)
admin.site.register(PoliticalParty)