import datetime
import logging
import uuid
import os

import requests

from django.db import transaction

import scraper.besluitenlijst

from document.models import BesluitItem
from document.models import BesluitItemCase
from document.models import BesluitenLijst

from pdfminer.pdfparser import PDFSyntaxError

from openkamer import settings


logger = logging.getLogger(__name__)


# def create_besluitenlijsten(max_commissions=None, max_results_per_commission=None, skip_existing=False):
#     logger.info('BEGIN')
#     besluiten_lijsten = []
#     commissies = scraper.besluitenlijst.get_voortouwcommissies_besluiten_urls()
#     for index, commissie in enumerate(commissies):
#         urls = scraper.besluitenlijst.get_besluitenlijsten_urls(commissie['url'], max_results=max_results_per_commission)
#         for url in urls:
#             if skip_existing and BesluitenLijst.objects.filter(url=url).exists():
#                 logger.info('besluitenlijst already exists, skip')
#                 continue
#             try:
#                 besluiten_lijst = create_besluitenlijst(url)
#                 besluiten_lijsten.append(besluiten_lijst)
#             except PDFSyntaxError as e:
#                 logger.error('failed to download and parse besluitenlijst with url: ' + url)
#             except TypeError as error:
#                 # pdfminer error that may cause this has been reported here: https://github.com/euske/pdfminer/pull/89
#                 logger.error('error while converting besluitenlijst pdf to text')
#                 logger.exception(error)
#             except Exception as error:
#                 logger.error('failed to download and parse besluitenlijst with url: ' + url)
#                 logger.exception(error)
#                 raise
#         if max_commissions and (index+1) >= max_commissions:
#             break
#     logger.info('END')
#     return besluiten_lijsten


@transaction.atomic
def create_besluitenlijst(url):
    logger.info('BEGIN')
    logger.info('url: ' + url)
    filename = uuid.uuid4().hex + '.pdf'
    filepath = os.path.join(settings.OK_TMP_DIR, filename)
    with open(filepath, 'wb') as pdffile:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        pdffile.write(response.content)
    text = scraper.besluitenlijst.besluitenlijst_pdf_to_text(filepath)
    os.remove(filepath)
    bl = scraper.besluitenlijst.create_besluitenlijst(text)
    BesluitenLijst.objects.filter(activity_id=bl.activiteitnummer).delete()
    BesluitenLijst.objects.filter(url=url).delete()
    besluiten_lijst = BesluitenLijst.objects.create(
        title=bl.title,
        commission=bl.voortouwcommissie,
        activity_id=bl.activiteitnummer,
        date_published=bl.date_published,
        url=url
    )

    for item in bl.items:
        besluit_item = BesluitItem.objects.create(
            title=item.title,
            besluiten_lijst=besluiten_lijst
        )
        for case in item.cases:
            BesluitItemCase.objects.create(
                title=case.title,
                besluit_item=besluit_item,
                decisions=case.create_str_list(case.decisions, BesluitItemCase.SEP_CHAR),
                notes=case.create_str_list(case.notes, BesluitItemCase.SEP_CHAR),
                related_commissions=case.create_str_list(case.volgcommissies, BesluitItemCase.SEP_CHAR),
                related_document_ids=case.create_str_list(case.related_document_ids, BesluitItemCase.SEP_CHAR),
            )
    logger.info('END')
    return besluiten_lijst
