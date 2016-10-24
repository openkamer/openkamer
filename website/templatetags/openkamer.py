import datetime
from django import template

from document.models import Kamerstuk
from document.models import Voting
from parliament.models import PartyMember

register = template.Library()


@register.assignment_tag
def get_current_party(person_id):
    members = PartyMember.objects.filter(person=person_id)
    for member in members:
        if member.left is None:
            return member.party
    return None


@register.assignment_tag
def get_kamerstuk_icon_name(kamerstuk_id):
    kamerstuk = Kamerstuk.objects.get(id=kamerstuk_id)
    if kamerstuk.type() == Kamerstuk.MOTIE:
        return 'fa-ticket'
    elif kamerstuk.type() == Kamerstuk.AMENDEMENT:
        return 'fa-pencil'
    elif kamerstuk.type() == Kamerstuk.WETSVOORSTEL:
        return 'fa-balance-scale'
    elif kamerstuk.type() == Kamerstuk.VERSLAG:
        return 'fa-comments'
    elif kamerstuk.type() == Kamerstuk.NOTA:
        # return 'fa-sticky-note'
        return 'fa-bullhorn'
    return 'fa-file-text'


@register.assignment_tag
def get_kamerstuk_timeline_bg_color(kamerstuk_id):
    kamerstuk = Kamerstuk.objects.get(id=kamerstuk_id)
    voting = kamerstuk.voting()
    if not voting:
        return 'bg-info'
    if voting.result == Voting.VERWORPEN:
        return 'bg-danger'
    elif voting.result == Voting.AANGENOMEN:
        return 'bg-success'
    elif voting.result == Voting.INGETROKKEN:
        return 'bg-warning'
    elif voting.result == Voting.AANGEHOUDEN:
        return 'bg-warning'
    return 'bg-info'
