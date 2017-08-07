import logging

from django.db import transaction

from document.models import Agenda
from document.models import AgendaItem

from document.models import Dossier

logger = logging.getLogger(__name__)



@transaction.atomic
def create_agenda(document, metadata):
    logger.info('create agenda')
    agenda = Agenda.objects.create(
        agenda_id=document.document_id,
        document=document,
    )
    agenda_items = []
    for n in metadata['behandelde_dossiers']:
        dossiers = Dossier.objects.filter(dossier_id=n)
        if dossiers:
            dossier = dossiers[0]
            agenda_item = AgendaItem(
                agenda=agenda,
                dossier=dossier,
                item_text=n,
            )
        else:
            agenda_item = AgendaItem(
                agenda=agenda,
                item_text=n,
            )
        agenda_items.append(agenda_item)
    AgendaItem.objects.bulk_create(agenda_items)
    return agenda


def create_or_update_agenda(agenda_id):
    #TODO: implement
    agendas = Agenda.objects.filter(agenda_id=agenda_id)
    if agendas:
        #        pass
        agenda = agendas[0]
        agenda.document.delete()
        agenda.delete()
    else:
        pass

    return
