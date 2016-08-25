from django.contrib import admin

from voting.models import Vote, Voting


class VotingAdmin(admin.ModelAdmin):
    list_display = ('dossier', 'result', 'date', 'kamerstuk')


class VoteAdmin(admin.ModelAdmin):
    list_display = ('voting', 'party', 'number_of_seats', 'details')


admin.site.register(Voting, VotingAdmin)
admin.site.register(Vote, VoteAdmin)
