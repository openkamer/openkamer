import logging
import re
import datetime
from typing import List

from django.db import transaction

import tkapi
from tkapi.document import Document as TKDocument
from tkapi.document import VerslagAlgemeenOverleg

from document.models import CommissieDocument
from document.models import Dossier
from document.models import Kamerstuk
from parliament.models import Commissie

from openkamer.document import DocumentFactory

logger = logging.getLogger(__name__)


def create_verslagen_algemeen_overleg(year, max_n=None, skip_if_exists=False):
    logger.info('BEGIN: {}'.format(year))
    year = int(year)
    begin_datetime = datetime.datetime(year=year, month=1, day=1)
    end_datetime = datetime.datetime(year=year+1, month=1, day=1)
    tk_verslagen = get_tk_verlag_algemeen_overleg(begin_datetime, end_datetime)
    counter = 1
    for tk_verslag in tk_verslagen:
        try:
            create_verslag_ao(tk_verslag, skip_if_exists=skip_if_exists)
        except Exception as error:
            logger.error('error for kamervraag id: {}'.format(tk_verslag.document_url))
            logger.exception(error)
        if max_n and counter >= max_n:
            return
        counter += 1
    logger.info('END: {}'.format(year))


def create_verslag_ao(tk_verslag, skip_if_exists=False):
    dossier = tk_verslag.dossiers[0]
    dossier_id = Dossier.create_dossier_id(dossier.nummer, dossier.toevoeging)
    name = tk_verslag.voortouwcommissie_namen[0] if tk_verslag.voortouwcommissie_namen else ''
    logger.info('commissie name: {}'.format(name))
    name_short = Commissie.create_short_name(name)
    slug = Commissie.create_slug(name_short)
    commissie, created = Commissie.objects.get_or_create(name=name, name_short=name_short, slug=slug)
    commissie_document = create_verslag(
        tk_document=tk_verslag,
        overheidnl_document_id=tk_verslag.document_url.replace('https://zoek.officielebekendmakingen.nl/', ''),
        dossier_id=dossier_id,
        kamerstuk_nr=tk_verslag.volgnummer,
        commissie=commissie,
        skip_if_exists=skip_if_exists,
    )
    return commissie_document


@transaction.atomic
def create_verslag(tk_document: TKDocument, overheidnl_document_id, dossier_id, kamerstuk_nr, commissie, skip_if_exists=False):
    if skip_if_exists and Kamerstuk.objects.filter(document__document_id=overheidnl_document_id).exists():
        return
    document_factory = DocumentFactory()
    document, metadata = document_factory.create_document(tk_document, overheidnl_document_id, dossier_id=dossier_id)
    document.title_short = get_verslag_document_title(document.title_short)
    document.save()
    Kamerstuk.objects.filter(document=document).delete()
    kamerstuk = Kamerstuk.objects.create(
        document=document,
        id_main=dossier_id,
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


def get_tk_verlag_algemeen_overleg(begin_datetime, end_datetime) -> List[VerslagAlgemeenOverleg]:
    pd_filter = TKDocument.create_filter()
    pd_filter.filter_date_range(begin_datetime, end_datetime)
    tk_verslagen = tkapi.Api().get_verslagen_van_algemeen_overleg(pd_filter)
    return tk_verslagen
