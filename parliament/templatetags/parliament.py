import datetime
from django import template

from parliament.models import ParliamentMember

register = template.Library()


@register.simple_tag
def parliament_member_id(member_name):
    # TODO: implement and test
    has_initials = len(member_name.split('.')) > 1
    initials = ''
    if has_initials:
        initials = member_name.split(' ')[0]
        surname = member_name.split(' ')[1]
    member = ParliamentMember.find(surname=surname, initials=initials)
    if member:
        return member.id
    return None
