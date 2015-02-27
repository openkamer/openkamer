
import logging
logger = logging.getLogger(__name__)

from django.contrib import admin

from voting.models import Bill, Vote, Member, Party


class BillAdmin(admin.ModelAdmin):
    model = Bill
    list_display = ('title', 'author', 'type', 'datetime')


class MemberAdmin(admin.ModelAdmin):
    model = Member
    list_display = ('name', 'party')


class PartyAdmin(admin.ModelAdmin):
    model = Party
    list_display = ('name', 'seats')


class VoteAdmin(admin.ModelAdmin):
    model = Vote
    list_display = ('bill', 'party', 'decision', 'details')


admin.site.register(Bill, BillAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Party, PartyAdmin)
admin.site.register(Vote, VoteAdmin)
