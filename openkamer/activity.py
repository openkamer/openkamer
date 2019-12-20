import logging
from typing import List

from django.db import transaction

from tkapi.util import queries

from document.models import Dossier
from document.models import Activity
from document.models import Decision

logger = logging.getLogger(__name__)


@transaction.atomic
def create_dossier_activities(dossier_id_main: str, dossier_id_sub: str, dossier: Dossier) -> List[Activity]:
    logger.info('BEGIN')
    tk_activities = queries.get_dossier_activiteiten(nummer=dossier_id_main, toevoeging=dossier_id_sub, include_agendapunten=True)
    logger.info('tk_activities found: {}'.format(len(tk_activities)))

    activities = []
    for tk_activity in tk_activities:
        # kamerstuk = Kamerstuk.objects.filter(
        #     id_main=dossier.dossier_id,
        #     id_sub=tk_besluit.zaak.volgnummer
        # ).first()

        # for tk_agendaitem in tk_activity.agendapunten:
        #     for tk_document in tk_agendaitem.documenten:
        #         print('tk_agendaitem.tk_document', tk_document.onderwerp)

        activity, created = Activity.objects.update_or_create(
            tk_id=tk_activity.id,
            dossier=dossier,
            # kamerstuk=kamerstuk,
            status=tk_activity.status.name,
            type=tk_activity.soort.name,
            subject=tk_activity.onderwerp,
            datetime=tk_activity.datum,
            begin=tk_activity.begin,
            end=tk_activity.einde,
        )
        for tk_agendaitem in tk_activity.agendapunten:
            if tk_agendaitem.besluit:
                decision = Decision.objects.filter(tk_id=tk_agendaitem.besluit.id).first()
                if decision is not None:
                    continue
                decision.activity = activity
                decision.save()
        activities.append(activity)
    logger.info('END: {} activities created'.format(len(activities)))
    return activities
