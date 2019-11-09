import logging

from tkapi import Api
from tkapi.zaak import Zaak
from tkapi.zaak import ZaakSoort

logger = logging.getLogger(__name__)


def get_dossier_ids():
    filter = Zaak.create_filter()
    filter.filter_soort(ZaakSoort.WETGEVING, is_or=True)
    filter.filter_soort(ZaakSoort.INITIATIEF_WETGEVING, is_or=True)
    # TODO BR: enable when dossier toevoeging is possible
    # filter.filter_soort('Begroting', is_or=True)
    zaken = Api.get_zaken(filter=filter)
    dossier_ids = set()
    for zaak in zaken:
        dossier_id = str(zaak.dossier.nummer)
        if zaak.dossier.toevoeging:
            dossier_id += '-' + str(zaak.dossier.toevoeging)
            # TODO BR: for now we cannot handle these
            logger.warning('Skipping dossier id with toevoeging: {}'.format(dossier_id))
            continue
        logger.info('dossier id: {}'.format(dossier_id))
        dossier_ids.add(dossier_id)
    return sorted(list(dossier_ids))
