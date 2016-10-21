import datetime
from django import template

from parliament.models import PartyMember

register = template.Library()


@register.assignment_tag
def get_current_party(person_id):
    members = PartyMember.objects.filter(person=person_id)
    for member in members:
        if member.left is None:
            return member.party
    return None
