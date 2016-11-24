import datetime
from django import template

from document.models import Dossier
from document.models import Kamerstuk
from document.models import Voting
from parliament.models import PartyMember

register = template.Library()


@register.assignment_tag
def get_dossier_exists(dossier_id):
    return Dossier.objects.filter(dossier_id=dossier_id).exists()


@register.assignment_tag
def get_current_party(person_id):
    members = PartyMember.objects.filter(person=person_id).select_related('party', 'person')
    for member in members:
        if member.left is None:
            return member.party
    return None


@register.assignment_tag
def get_kamerstuk_icon_name(kamerstuk):
    if kamerstuk.type == Kamerstuk.MOTIE:
        return 'fa-ticket'
    elif kamerstuk.type == Kamerstuk.AMENDEMENT:
        return 'fa-pencil'
    elif kamerstuk.type == Kamerstuk.WETSVOORSTEL:
        return 'fa-balance-scale'
    elif kamerstuk.type == Kamerstuk.VERSLAG:
        return 'fa-comments'
    elif kamerstuk.type == Kamerstuk.NOTA:
        return 'fa-file'
    elif kamerstuk.type == Kamerstuk.BRIEF:
        return 'fa-envelope'
    return 'fa-file-text'


@register.assignment_tag
def get_kamerstuk_timeline_bg_color(kamerstuk):
    voting = kamerstuk.voting
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


@register.assignment_tag
def get_voting_result_color(voting):
    if not voting:
        return 'info'
    if voting.result == Voting.VERWORPEN:
        return 'danger'
    elif voting.result == Voting.AANGENOMEN:
        return 'success'
    elif voting.result == Voting.INGETROKKEN:
        return 'warning'
    elif voting.result == Voting.AANGEHOUDEN:
        return 'warning'
    return 'info'


@register.assignment_tag
def get_voting_result_icon(voting):
    if not voting:
        return 'fa-spinner'
    if voting.result == Voting.VERWORPEN:
        return 'fa-times'
    elif voting.result == Voting.AANGENOMEN:
        return 'fa-check'
    elif voting.result == Voting.INGETROKKEN:
        return 'fa-undo'
    elif voting.result == Voting.AANGEHOUDEN:
        return 'fa-pause'
    return 'fa-spinner'


@register.assignment_tag
def get_extra_category_button_class(category_slug, active_category_slug):
    if category_slug == active_category_slug:
        return 'active'
    elif category_slug.lower() == 'all' and active_category_slug == '':
        return 'active'
    return ''
