
import logging
logger = logging.getLogger(__name__)

from django.contrib import admin

from voting.models import Bill, Vote


class BillAdmin(admin.ModelAdmin):
    model = Bill
    list_display = ('title', 'author', 'type', 'datetime')


class VoteAdmin(admin.ModelAdmin):
    model = Vote
    list_display = ('bill', 'party', 'decision', 'details')


admin.site.register(Bill, BillAdmin)
admin.site.register(Vote, VoteAdmin)
