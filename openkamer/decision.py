import logging

from django.db import transaction

from tkapi.util import queries

from document.models import Dossier
from document.models import Decision
from document.models import Kamerstuk

logger = logging.getLogger(__name__)


@transaction.atomic
def create_dossier_decisions(dossier_id_main: str, dossier_id_sub: str, dossier: Dossier):
    logger.info('BEGIN')
    tk_besluiten = queries.get_dossier_besluiten(nummer=dossier_id_main, toevoeging=dossier_id_sub)
    decisions = []
    for tk_besluit in tk_besluiten:
        kamerstuk = Kamerstuk.objects.filter(
            id_main=dossier.dossier_id,
            id_sub=tk_besluit.zaak.volgnummer
        ).first()
        decision = Decision.objects.update_or_create(
            tk_id=tk_besluit.id,
            dossier=dossier,
            kamerstuk=kamerstuk,
            status=tk_besluit.status,
            text=tk_besluit.tekst,
            type=tk_besluit.type,
            note=tk_besluit.opmerking,
            datetime=tk_besluit.agendapunt.activiteit.datum,
        )
        decisions.append(decision)
    logger.info('END: {} decisions created'.format(len(decisions)))
    return decisions
