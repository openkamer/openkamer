import logging
import re

import time
from typing import List

from requests.exceptions import ConnectTimeout
from requests.exceptions import ConnectionError

from django.db import transaction

from tkapi import TKApi
from tkapi.util import queries
from tkapi.persoon import Persoon as TKPersoon
from tkapi.dossier import Dossier as TKDossier
from tkapi.document import Document as TKDocument
from tkapi.besluit import Besluit as TKBesluit
from tkapi.zaak import Zaak
from tkapi.zaak import ZaakSoort
from tkapi.activiteit import ActiviteitStatus

import scraper.documents

from document.create import get_dossier_ids, DossierId
from document.models import CategoryDossier
from document.models import Dossier
from document.models import Kamerstuk

from openkamer.document import DocumentFactory
from openkamer.document import DocumentData
from openkamer.document import get_categories
from openkamer.decision import create_dossier_decisions
from openkamer.kamerstuk import create_kamerstuk
from openkamer.voting import VotingFactory

logger = logging.getLogger(__name__)


def create_dossier_retry_on_error(dossier_id, max_tries=3):
    dossier_id = str(dossier_id)
    tries = 0
    while True:
        try:
            tries += 1
            create_or_update_dossier(dossier_id)
        except (ConnectionError, ConnectTimeout) as error:
            logger.exception(error)
            time.sleep(5)  # wait 5 seconds for external servers to relax
            if tries < max_tries:
                logger.error('trying again!')
                continue
            logger.error('max tries reached, skipping dossier: ' + dossier_id)
        break


@transaction.atomic
def create_or_update_dossier(dossier_id):
    logger.info('BEGIN - dossier id: {}'.format(dossier_id))
    Dossier.objects.filter(dossier_id=dossier_id).delete()
    dossier_url = 'https://zoek.officielebekendmakingen.nl/dossier/{}'.format(dossier_id)
    dossier_id_main, dossier_id_sub = Dossier.split_dossier_id(dossier_id)

    dossier_filter = TKDossier.create_filter()
    dossier_filter.filter_nummer(dossier_id_main)
    if dossier_id_sub:
        dossier_filter.filter_toevoeging(dossier_id_sub)
    dossiers = TKApi.get_dossiers(filter=dossier_filter)

    if len(dossiers) != 1:
        logger.error('{} dossiers found while one expected for {}'.format(len(dossiers), dossier_id))

    tk_dossier = dossiers[0]

    # TODO BR: create a list of related dossier decisions instead of one, see dossier 34792 for example
    logger.info('dossier id main: {} | dossier id sub: {}'.format(dossier_id_main, dossier_id_sub))
    last_besluit = get_besluit_last_with_voting(dossier_id_main, dossier_id_sub)
    if not last_besluit:
        last_besluit = get_besluit_last(dossier_id_main, dossier_id_sub)

    decision_text = 'Onbekend'
    if last_besluit:
        decision_text = last_besluit.tekst.replace('.', '')

    dossier_new = Dossier.objects.create(
        dossier_id=dossier_id,
        dossier_main_id=dossier_id_main,
        dossier_sub_id=dossier_id_sub,
        title=tk_dossier.titel,
        url=dossier_url,
        decision_text=decision_text
    )
    create_dossier_documents(dossier_new, dossier_id)
    create_dossier_decisions(dossier_id_main, dossier_id_sub, dossier_new)
    voting_factory = VotingFactory()
    voting_factory.create_votings(dossier_id)
    dossier_new.set_derived_fields()
    logger.info('END - dossier id: ' + str(dossier_id))
    return dossier_new


def get_document_data(tk_document: TKDocument, tk_zaak: Zaak, dossier_id):
    dossier_id = re.sub(r'-\(.*\)', '', dossier_id)  # Rijkswet ID is not used in url
    overheid_document_id = 'kst-{}-{}'.format(dossier_id, tk_document.volgnummer)
    metadata = scraper.documents.get_metadata(overheid_document_id)

    try:
        content_html = scraper.documents.get_html_content(overheid_document_id)
    except:
        logger.exception('error getting document html for document id: {}'.format(overheid_document_id))
        content_html = ''
    document_data = DocumentData(
        document_id=overheid_document_id,
        tk_document=tk_document,
        tk_zaak=tk_zaak,
        metadata=metadata,
        content_html=content_html,
    )
    return document_data


@transaction.atomic
def create_dossier_documents(dossier, dossier_id):
    logger.info('create_dossier_documents - BEGIN')

    tk_dossier = queries.get_dossier(nummer=dossier.dossier_main_id, toevoeging=dossier.dossier_sub_id)

    outputs = []
    for tk_zaak in tk_dossier.zaken:
        for doc in tk_zaak.documenten:
            if int(doc.volgnummer) == -1:
                # TODO BR: this document is not found at overheid.nl, fix this
                continue
            outputs.append(get_document_data(doc, tk_zaak, dossier_id))

    logger.info('create_dossier_documents - outputs: {}'.format(len(outputs)))

    for data in outputs:
        properties = {
            'dossier': dossier,
            'title_full': data.tk_document.onderwerp,
            'title_short': data.tk_document.onderwerp,
            'publication_type': data.tk_document.soort.value,
            'date_published': data.tk_document.datum,
            'source_url': data.url,
            'content_html': data.content_html,
        }

        document = DocumentFactory.create_or_update_document(data, properties)

        if not Kamerstuk.objects.filter(id_main=dossier_id, id_sub=data.tk_document.volgnummer).exists():
            create_kamerstuk(
                document=document,
                dossier_id=dossier_id,
                number=data.tk_document.volgnummer,
                type_long=data.tk_document.onderwerp,
                type_short=data.tk_document.soort.value
            )
            category_list = get_categories(text=data.category, category_class=CategoryDossier, sep_char='|')
            dossier.categories.add(*category_list)


def get_inactive_dossier_ids(year=None) -> List[DossierId]:
    dossier_ids_inactive = list(Dossier.objects.filter(status__in=[
        Dossier.VERWORPEN, Dossier.AANGENOMEN, Dossier.INGETROKKEN, Dossier.CONTROVERSIEEL
    ]).values_list('dossier_id', flat=True))
    if year is not None:
        dossier_ids_inactive_year = []
        for dossier_id in dossier_ids_inactive:
            dossier = Dossier.objects.get(dossier_id=dossier_id)
            if dossier.start_date and dossier.start_date.year == int(year):
                dossier_ids_inactive_year.append(dossier_id)
        dossier_ids_inactive = dossier_ids_inactive_year
    return [DossierId(*Dossier.split_dossier_id(dossier_id)) for dossier_id in dossier_ids_inactive]


def create_wetsvoorstellen_active(skip_existing=False, max_tries=3):
    logger.info('BEGIN')
    dossiers = get_dossier_ids()
    logger.info('active dossiers found: {}'.format(len(dossiers)))
    dossier_ids_inactive = get_inactive_dossier_ids()
    dossier_ids_inactive = [str(dossier_id) for dossier_id in dossier_ids_inactive]
    dossier_ids_active = []
    for dossier in dossiers:
        if str(dossier) not in dossier_ids_inactive:
            dossier_ids_active.append(dossier)
    dossier_ids_active.reverse()
    logger.info('dossiers active: {}'.format(dossier_ids_active))
    failed_dossiers = create_wetsvoorstellen(dossier_ids_active, skip_existing=skip_existing, max_tries=max_tries)
    logger.info('END')
    return failed_dossiers


def create_wetsvoorstellen_inactive(year=None, skip_existing=False, max_tries=3):
    logger.info('BEGIN - year: {}'.format(year))
    dossier_ids_inactive = get_inactive_dossier_ids(year=year)
    dossier_ids_inactive.reverse()
    logger.info('inactive dossiers found: {}'.format(len(dossier_ids_inactive)))
    failed_dossiers = create_wetsvoorstellen(dossier_ids_inactive, skip_existing=skip_existing, max_tries=max_tries)
    logger.info('END')
    return failed_dossiers


def create_wetsvoorstellen_all(skip_existing=False, max_tries=3):
    logger.info('BEGIN')
    dossier_ids = get_dossier_ids()
    dossier_ids.reverse()
    failed_dossiers = create_wetsvoorstellen(dossier_ids, skip_existing=skip_existing, max_tries=max_tries)
    logger.info('END')
    return failed_dossiers


def create_wetsvoorstellen(dossier_ids: List[DossierId], skip_existing=False, max_tries=3):
    logger.info('BEGIN')
    failed_dossiers = []
    for dossier in dossier_ids:
        dossier_id = Dossier.create_dossier_id(dossier.dossier_id, dossier.dossier_sub_id)
        logger.info('dossier id: {}'.format(dossier_id))
        dossiers = Dossier.objects.filter(dossier_id=dossier_id)
        if skip_existing and dossiers.exists():
            logger.info('dossier already exists, skip')
            continue
        try:
            create_dossier_retry_on_error(dossier_id=dossier_id, max_tries=max_tries)
        except Exception as error:
            failed_dossiers.append(dossier_id)
            logger.exception('error for dossier id: ' + str(dossier_id))
    logger.info('END')
    return failed_dossiers


def get_tk_besluiten_dossier_main(dossier_id_main, dossier_id_sub=None) -> List[TKBesluit]:
    tk_besluiten = queries.get_dossier_besluiten(nummer=dossier_id_main, toevoeging=dossier_id_sub)
    besluiten_dossier = []
    # only get main dossier besluiten; ignore kamerstuk besluiten (motie, amendement, etc)
    for tk_besluit in tk_besluiten:
        if str(tk_besluit.zaak.volgnummer) == '0':
            besluiten_dossier.append(tk_besluit)
    return besluiten_dossier


def get_besluit_last(dossier_id_main, dossier_id_sub=None, filter_has_votings=False) -> TKBesluit:
    tk_besluiten = get_tk_besluiten_dossier_main(dossier_id_main=dossier_id_main, dossier_id_sub=dossier_id_sub)
    last_besluit = None
    for tk_besluit in tk_besluiten:
        if filter_has_votings and not tk_besluit.stemmingen:
            continue
        if tk_besluit.agendapunt.activiteit.status == ActiviteitStatus.GEPLAND:
            # TODO: create dossier agendapunt with planned activiteit
            continue
        if last_besluit is None or tk_besluit.agendapunt.activiteit.begin > last_besluit.agendapunt.activiteit.begin:
            last_besluit = tk_besluit
    return last_besluit


def get_besluit_last_with_voting(dossier_id_main, dossier_id_sub=None) -> TKBesluit:
    return get_besluit_last(dossier_id_main=dossier_id_main, dossier_id_sub=dossier_id_sub, filter_has_votings=True)


def get_zaken_dossier_main(dossier_id_main, dossier_id_sub=None) -> List[Zaak]:
    # TODO BR: filter by Wetgeving OR Initiatiefwetgeving if tkapi makes it possible
    filter = Zaak.create_filter()
    filter.filter_kamerstukdossier(nummer=dossier_id_main, toevoeging=dossier_id_sub)
    filter.filter_soort(ZaakSoort.WETGEVING)
    zaken = TKApi.get_zaken(filter=filter)
    if not zaken:
        filter = Zaak.create_filter()
        filter.filter_kamerstukdossier(nummer=dossier_id_main, toevoeging=dossier_id_sub)
        filter.filter_soort(ZaakSoort.INITIATIEF_WETGEVING)
        zaken = TKApi.get_zaken(filter=filter)
    if not zaken:
        filter = Zaak.create_filter()
        filter.filter_kamerstukdossier(nummer=dossier_id_main, toevoeging=dossier_id_sub)
        filter.filter_soort(ZaakSoort.BEGROTING)
        zaken = TKApi.get_zaken(filter=filter)
    return zaken
