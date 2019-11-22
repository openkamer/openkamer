import logging
import re
import datetime
from typing import List

from django.db import transaction

import tkapi
import tkapi.document

from document.models import Kamerstuk
from document.models import CommissieDocument
from parliament.models import Commissie

from openkamer.document import DocumentFactory

logger = logging.getLogger(__name__)


def create_verslagen_algemeen_overleg(year, max_n=None, skip_if_exists=False):
    logger.info('BEGIN')
    begin_datetime = datetime.datetime(year=year, month=1, day=1)
    end_datetime = datetime.datetime(year=year+1, month=1, day=1)
    tk_verslagen = get_tk_verlag_algemeen_overleg(begin_datetime, end_datetime)
    counter = 1
    for tk_verslag in tk_verslagen:
        try:
            dossier = tk_verslag.dossiers[0]
            dossier_id = str(dossier.nummer)
            dossier_id_extra = ''
            if dossier.toevoeging:
                dossier_id_extra = str(dossier.toevoeging)
            name = tk_verslag.voortouwcommissie_namen[0] if tk_verslag.voortouwcommissie_namen else ''
            logger.info('commissie name: {}'.format(name))
            name_short = Commissie.create_short_name(name)
            slug = Commissie.create_slug(name_short)
            commissie, created = Commissie.objects.get_or_create(name=name, name_short=name_short, slug=slug)
            commissie_document = create_verslag(
                overheidnl_document_id=tk_verslag.document_url.replace('https://zoek.officielebekendmakingen.nl/', ''),
                dossier_id=dossier_id,
                dossier_id_extra=dossier_id_extra,
                kamerstuk_nr=tk_verslag.volgnummer,
                commissie=commissie,
                skip_if_exists=skip_if_exists,
            )
        except Exception as error:
            logger.error('error for kamervraag id: {}'.format(tk_verslag.document_url))
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


def get_tk_verlag_algemeen_overleg(begin_datetime, end_datetime) -> List[tkapi.document.VerslagAlgemeenOverleg]:
    pd_filter = tkapi.document.Document.create_filter()
    pd_filter.filter_date_range(begin_datetime, end_datetime)
    tk_verslagen = tkapi.Api().get_verslagen_van_algemeen_overleg(pd_filter)
    return tk_verslagen
