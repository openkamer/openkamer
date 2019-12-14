import logging
from typing import List

from tkapi import TKApi
from tkapi.zaak import Zaak
from tkapi.zaak import ZaakSoort

logger = logging.getLogger(__name__)


class DossierId:
    dossier_id = None
    dossier_sub_id = None

    def __init__(self, dossier_id, dossier_sub_id=None):
        self.dossier_id = dossier_id
        self.dossier_sub_id = dossier_sub_id

    def __str__(self):
        dossier_id_str = self.dossier_id
        if self.dossier_sub_id:
            dossier_id_str += '-' + self.dossier_sub_id
        return dossier_id_str

    def __hash__(self):
        return hash('{}-{}'.format(self.dossier_id, self.dossier_sub_id))


def get_dossier_ids() -> List[DossierId]:
    filter = Zaak.create_filter()
    filter.filter_soort(ZaakSoort.WETGEVING, is_or=True)
    filter.filter_soort(ZaakSoort.INITIATIEF_WETGEVING, is_or=True)
    filter.filter_soort(ZaakSoort.BEGROTING, is_or=True)
    zaken = TKApi.get_zaken(filter=filter)
    dossier_ids = set()
    for zaak in zaken:
        dossier_id = str(zaak.dossier.nummer)
        dossier_sub_id = zaak.dossier.toevoeging
        dossier_ids.add(DossierId(dossier_id, dossier_sub_id))
    return list(dossier_ids)
