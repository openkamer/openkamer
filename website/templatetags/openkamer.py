import datetime
from django import template

from document.models import Dossier
from document.models import Document
from document.models import Kamerstuk
from document.models import Submitter
from document.models import Voting
from parliament.models import PartyMember
from parliament.models import ParliamentMember
from government.models import GovernmentMember

register = template.Library()


@register.assignment_tag
def get_dossier_exists(dossier_id):
    return Dossier.objects.filter(dossier_id=dossier_id).exists()


@register.assignment_tag
def get_current_party(person_id):
    members = PartyMember.objects.filter(person=person_id, left__isnull=True).select_related('party', 'person').order_by('-joined')
    if members.exists():
        return members[0].party
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
    elif voting.result == Voting.CONTROVERSIEEL:
        return 'bg-warning'
    return 'bg-info'


@register.assignment_tag
def get_dossier_status_color(dossier):
    if not dossier:
        return 'info'
    if dossier.status == Dossier.VERWORPEN:
        return 'danger'
    elif dossier.status == Dossier.AANGENOMEN:
        return 'success'
    elif dossier.status == Dossier.INGETROKKEN:
        return 'warning'
    elif dossier.status == Dossier.AANGEHOUDEN:
        return 'warning'
    elif dossier.status == Dossier.CONTROVERSIEEL:
        return 'warning'
    elif dossier.status == Dossier.IN_BEHANDELING:
        return 'info'
    elif dossier.status == Dossier.ONBEKEND:
        return 'info'
    return 'info'


@register.assignment_tag
def get_dossier_status_icon(dossier):
    if not dossier:
        return 'fa-spinner'
    if dossier.status == Dossier.VERWORPEN:
        return 'fa-times'
    elif dossier.status == Dossier.AANGENOMEN:
        return 'fa-check'
    elif dossier.status == Dossier.INGETROKKEN:
        return 'fa-undo'
    elif dossier.status == Dossier.AANGEHOUDEN:
        return 'fa-pause'
    elif dossier.status == Dossier.CONTROVERSIEEL:
        return 'fa-warning'
    elif dossier.status == Dossier.IN_BEHANDELING:
        return 'fa-spinner'
    elif dossier.status == Dossier.ONBEKEND:
        return 'fa-question'
    return 'fa-spinner'


@register.assignment_tag
def get_extra_category_button_class(category_slug, active_category_slug):
    if category_slug == active_category_slug:
        return 'active'
    elif category_slug.lower() == 'all' and active_category_slug == '':
        return 'active'
    return ''


@register.assignment_tag
def get_submitters(person):
    return Submitter.objects.filter(person=person)


@register.assignment_tag
def get_government_members_for_person(person):
    return GovernmentMember.objects.filter(person=person).order_by('-start_date')


@register.assignment_tag
def get_parliament_members_for_person(person):
    return ParliamentMember.objects.filter(person=person).order_by('-joined')


@register.assignment_tag
def get_party_members_for_person(person):
    return PartyMember.objects.filter(person=person)


@register.assignment_tag
def get_documents_for_person(person):
    submitters = Submitter.objects.filter(person=person)
    return Document.objects.filter(submitter__in=submitters)
