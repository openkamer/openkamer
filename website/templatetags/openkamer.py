import datetime
from django import template

from document.models import Dossier
from document.models import Document
from document.models import Kamerstuk
from document.models import Kamervraag
from document.models import Submitter
from document.models import Voting
from parliament.models import PartyMember
from parliament.models import ParliamentMember
from government.models import GovernmentMember
from gift.models import Gift

register = template.Library()


@register.simple_tag
def get_dossier_exists(dossier_id):
    return Dossier.objects.filter(dossier_id=dossier_id).exists()


@register.simple_tag
def get_current_party(person_id):
    members = PartyMember.objects.filter(person=person_id, left__isnull=True).select_related('party', 'person').order_by('-joined')
    if members.exists():
        return members[0].party
    return None


def get_submitter_ids(person):
    submitters = Submitter.objects.filter(person=person)
    submitter_ids = list(submitters.values_list('id', flat=True))
    return submitter_ids


@register.simple_tag
def get_submitters_parties(submitters):
    party_set = set()
    for submitter in submitters:
        if submitter.party:
            party_set.add(submitter.party)
    return party_set


@register.simple_tag
def get_activities(person):
    submitter_ids = get_submitter_ids(person)
    documents = Document.objects.filter(submitter__in=submitter_ids)
    kamervragen = Kamervraag.objects.filter(document__in=documents)
    kamerstukken = Kamerstuk.objects.filter(document__in=documents)
    moties = kamerstukken.filter(type=Kamerstuk.MOTIE)
    amendementen = kamerstukken.filter(type=Kamerstuk.AMENDEMENT)
    wetsvoorstellen = kamerstukken.filter(type=Kamerstuk.WETSVOORSTEL).select_related('dossier')
    dossier_ids = list(wetsvoorstellen.values_list('document__dossier_id', flat=True))
    wetsvoorstellen = Dossier.objects.filter(id__in=dossier_ids).distinct()
    activities = {
        'kamervragen': kamervragen,
        'moties': moties,
        'amendementen': amendementen,
        'wetsvoorstellen': wetsvoorstellen,
        'kamerstukken': kamerstukken,
    }
    return activities


@register.simple_tag
def get_kamervragen(person):
    submitter_ids = get_submitter_ids(person)
    kamervragen = Kamervraag.objects.filter(document__submitter__in=submitter_ids)
    return kamervragen


@register.simple_tag
def get_kamerstukken(person):
    submitter_ids = get_submitter_ids(person)
    kamerstukken = Kamerstuk.objects.filter(document__submitter__in=submitter_ids)
    return kamerstukken


@register.simple_tag
def get_moties(person):
    submitter_ids = get_submitter_ids(person)
    kamerstukken = Kamerstuk.objects.filter(document__submitter__in=submitter_ids, type=Kamerstuk.MOTIE)
    return kamerstukken


@register.simple_tag
def get_amendementen(person):
    submitter_ids = get_submitter_ids(person)
    kamerstukken = Kamerstuk.objects.filter(document__submitter__in=submitter_ids, type=Kamerstuk.AMENDEMENT)
    return kamerstukken


@register.simple_tag
def get_wetsvoorstellen(person):
    submitter_ids = get_submitter_ids(person)
    kamerstukken = Kamerstuk.objects.filter(document__submitter__in=submitter_ids, type=Kamerstuk.WETSVOORSTEL)
    dossier_ids = list(kamerstukken.values_list('document__dossier_id', flat=True))
    dossiers = Dossier.objects.filter(id__in=dossier_ids).distinct()
    return dossiers


@register.simple_tag
def get_dossiers_results(dossiers):
    aangenomen = dossiers.filter(status=Dossier.AANGENOMEN)
    verworpen = dossiers.filter(status=Dossier.VERWORPEN)
    in_behandeling = dossiers.filter(status=Dossier.IN_BEHANDELING) | dossiers.filter(status=Dossier.AANGEHOUDEN)
    results = creat_results(aangenomen, verworpen, in_behandeling)
    return results


@register.simple_tag
def get_kamerstukken_results(kamerstukken):
    aangenomen = kamerstukken.filter(voting__result=Voting.AANGENOMEN)
    verworpen = kamerstukken.filter(voting__result=Voting.VERWORPEN)
    results = creat_results(aangenomen, verworpen, None)
    return results


def creat_results(aangenomen, verworpen, in_behandeling):
    n_aangenomen = aangenomen.count()
    n_verworpen = verworpen.count()
    if in_behandeling:
        n_in_behandeling = in_behandeling.count()
    else:
        n_in_behandeling = 0
    n_total = n_aangenomen + n_verworpen + n_in_behandeling
    aangenomen_percent = 0
    verworpen_percent = 0
    in_behandeling_percent = 0
    if n_total != 0:
        aangenomen_percent = n_aangenomen/n_total * 100
        verworpen_percent = n_verworpen/n_total * 100
        in_behandeling_percent = n_in_behandeling/n_total * 100
    results = {
        'n_total': n_total,
        'n_aangenomen': n_aangenomen,
        'n_verworpen': n_verworpen,
        'n_in_behandeling': n_in_behandeling,
        'aangenomen_percent': aangenomen_percent,
        'verworpen_percent': verworpen_percent,
        'in_behandeling_percent': in_behandeling_percent
    }
    return results


@register.simple_tag
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


@register.simple_tag
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


@register.simple_tag
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


@register.simple_tag
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


@register.simple_tag
def get_extra_category_button_class(category_slug, active_category_slug):
    if category_slug == active_category_slug:
        return 'active'
    elif category_slug.lower() == 'all' and active_category_slug == '':
        return 'active'
    return ''


@register.simple_tag
def get_submitters(person):
    return Submitter.objects.filter(person=person)


@register.simple_tag
def get_government_members_for_person(person):
    return GovernmentMember.objects.filter(person=person).order_by('-start_date')


@register.simple_tag
def get_parliament_members_for_person(person):
    return ParliamentMember.objects.filter(person=person).order_by('-joined')


@register.simple_tag
def get_party_members_for_person(person):
    return PartyMember.objects.filter(person=person)


@register.simple_tag
def get_documents_for_person(person):
    submitters = Submitter.objects.filter(person=person)
    return Document.objects.filter(submitter__in=submitters)


@register.simple_tag
def get_gifts_for_person(person):
    gifts = Gift.objects.filter(person=person)
    return gifts
