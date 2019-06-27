import logging
import re
import csv
import requests

from django.db import transaction

from document.models import Dossier
from document.models import Kamerstuk
from document.models import CommissieDocument
from parliament.models import Commissie

from openkamer.document import DocumentFactory

logger = logging.getLogger(__name__)


def create_verslagen_algemeen_overleg(year, max_n=None, skip_if_exists=False):
    logger.info('BEGIN')
    infos = get_verlag_algemeen_overleg_infos(year)
    counter = 1
    for info in infos:
        try:
            dossier_id = str(info['dossier_id'])
            dossier_id_extra = str(info['dossier_extra_id'])
            name = info['commissie_name'].strip()
            logger.info('commissie name: {}'.format(name))
            name_short = Commissie.create_short_name(name)
            slug = Commissie.create_slug(name_short)
            commissie, created = Commissie.objects.get_or_create(name=name, name_short=name_short, slug=slug)
            commissie_document = create_verslag(
                overheidnl_document_id=info['document_url'].replace('https://zoek.officielebekendmakingen.nl/', ''),
                dossier_id=dossier_id,
                dossier_id_extra=dossier_id_extra,
                kamerstuk_nr=info['kamerstuk_nr'],
                commissie=commissie,
                skip_if_exists=skip_if_exists,
            )
        except Exception as error:
            logger.error('error for kamervraag id: ' + str(info['document_url']))
            logger.exception(error)
        if max_n and counter >= max_n:
            return
        counter += 1
    logger.info('END')


@transaction.atomic
def create_verslag(overheidnl_document_id, dossier_id, dossier_id_extra, kamerstuk_nr, commissie, skip_if_exists=False):
    if skip_if_exists and Kamerstuk.objects.filter(document__document_id=overheidnl_document_id).exists():
        return
    document_factory = DocumentFactory()
    document, metadata = document_factory.create_document(overheidnl_document_id, dossier_id=dossier_id)
    document.title_short = get_verslag_document_title(document.title_short)
    document.save()
    Kamerstuk.objects.filter(document=document).delete()
    kamerstuk = Kamerstuk.objects.create(
        document=document,
        id_main=dossier_id,
        id_main_extra=dossier_id_extra,
        id_sub=kamerstuk_nr,
        type_short='Verslag',
        type_long='Verslag van een algemeen overleg'
    )
    CommissieDocument.objects.filter(document=document).delete()
    verslag = CommissieDocument.objects.create(
        document=document,
        kamerstuk=kamerstuk,
        commissie=commissie
    )
    return verslag


def get_verslag_document_title(title):
    return upperfirst(re.sub(r'(Verslag van een algemeen overleg, gehouden.*? \d{4}, over )', '', title))


def upperfirst(x):
    return x[0].upper() + x[1:]


def get_verlag_algemeen_overleg_infos(year):
    url = 'https://raw.githubusercontent.com/openkamer/ok-tk-data/master/verslagen/verslagen_algemeen_overleg_{}.csv'.format(year)
    response = requests.get(url, timeout=60)
    rows = response.content.decode('utf-8').splitlines()
    rows = csv.reader(rows)
    next(rows, None)  # skip table headers
    verslagen_info = []
    for colums in rows:
        if colums[4] == '':  # no document url
            continue
        info = {
            'date_published': colums[0],
            'dossier_id': colums[1],
            'dossier_extra_id': colums[2],
            'kamerstuk_nr': colums[3],
            'document_url': str(colums[4]),
            'commissie_name': str(colums[5]),
        }
        logger.info('verslag info: {}'.format(info))
        verslagen_info.append(info)
    return verslagen_info
