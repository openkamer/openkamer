import logging
import re
import lxml

from django.db import transaction

from document.models import Dossier
from document.models import Kamerstuk

from .document import create_document

logger = logging.getLogger(__name__)


def create_verslagen_algemeen_overleg(year, max_n=None, skip_if_exists=False):
    logger.info('BEGIN')
    infos = get_verlag_algemeen_overleg_infos(year)
    counter = 1
    for info in infos:
        try:
            dossier_id = str(info['dossier_id'])
            dossier_id_extra = str(info['dossier_extra_id'])
            create_verslag(
                overheidnl_document_id=info['document_url'].replace('https://zoek.officielebekendmakingen.nl/', ''),
                dossier_id=dossier_id,
                dossier_id_extra=dossier_id_extra,
                kamerstuk_nr=info['kamerstuk_nr'],
                skip_if_exists=skip_if_exists)
        except Exception as error:
            logger.error('error for kamervraag id: ' + str(info['document_url']))
            logger.exception(error)
        if max_n and counter >= max_n:
            return
        counter += 1
    logger.info('END')


@transaction.atomic
def create_verslag(overheidnl_document_id, dossier_id, dossier_id_extra, kamerstuk_nr, skip_if_exists=False):
    if skip_if_exists and Kamerstuk.objects.filter(document__document_id=overheidnl_document_id).exists():
        return
    document, related_document_ids, metadata = create_document(overheidnl_document_id, dossier_id=dossier_id)
    document.title_short = get_verslag_document_title(document.title_short)
    document.save()
    Kamerstuk.objects.filter(document=document).delete()
    stuk = Kamerstuk.objects.create(
        document=document,
        id_main=dossier_id,
        id_main_extra=dossier_id_extra,
        id_sub=kamerstuk_nr,
        type_short='Verslag',
        type_long='Verslag van een algemeen overleg'
    )
    return stuk


def get_verslag_document_title(title):
    return re.sub(r'(Verslag van een algemeen overleg, gehouden.*? \d{4}, over )', '', title)


def get_verlag_algemeen_overleg_infos(year):
    lines = Dossier.get_lines_from_url(
        'https://raw.githubusercontent.com/openkamer/ok-tk-data/master/verslagen/verslagen_algemeen_overleg_' + str(year) + '.csv')
    lines.pop(0)  # remove table headers
    verslagen_info = []
    for line in lines:
        colums = line.split(',')
        if colums[4] == '':  # no document url
            continue
        info = {
            'date_published': colums[0],
            'dossier_id': colums[1],
            'dossier_extra_id': colums[2],
            'kamerstuk_nr': colums[3],
            'document_url': colums[4],
        }
        verslagen_info.append(info)
    return verslagen_info
