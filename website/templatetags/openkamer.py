import datetime
from django import template

from document.models import Kamerstuk
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
