import logging
import multiprocessing as mp
from multiprocessing.pool import ThreadPool
import time
from typing import List

from requests.exceptions import ConnectionError, ConnectTimeout

from django.db import transaction

from tkapi import Api
from tkapi.dossier import Dossier as TKDossier
from tkapi.besluit import Besluit
from tkapi.zaak import Zaak
from tkapi.zaak import ZaakSoort
from tkapi.activiteit import ActiviteitStatus

import scraper.documents

from document.create import get_dossier_ids, DossierId
from document.models import CategoryDossier
from document.models import Dossier
from document.models import Kamerstuk

from openkamer.document import update_document_html_links
from openkamer.document import DocumentFactory
from openkamer.document import DocumentData
from openkamer.document import get_categories
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
    dossiers = Api().get_dossiers(filter=dossier_filter)

    if len(dossiers) != 1:
        logger.error('{} dossiers found while one expected for {}'.format(len(dossiers), dossier_id))

    tk_dossier = dossiers[0]

    # TODO BR: create a list of related dossier decisions instead of one, see dossier 34792 for example
    logger.info('dossier id main: {} | dossier id sub: {}'.format(dossier_id_main, dossier_id_sub))
    last_besluit = get_besluit_last_with_voting(dossier_id_main, dossier_id_sub)
    if not last_besluit:
        last_besluit = get_besluit_last(dossier_id_main, dossier_id_sub)

    decision = 'Onbekend'
    if last_besluit:
        decision = last_besluit.tekst.replace('.', '')

    dossier_new = Dossier.objects.create(
        dossier_id=dossier_id,
        dossier_main_id=dossier_id_main,
        dossier_sub_id=dossier_id_sub,
        title=tk_dossier.titel,
        url=dossier_url,
        decision=decision
    )
    create_dossier_documents(dossier_new, dossier_id)
    voting_factory = VotingFactory()
    voting_factory.create_votings(dossier_id)
    dossier_new.set_derived_fields()
    logger.info('END - dossier id: ' + str(dossier_id))
    return dossier_new


class DocumentDataOverheidNL(object):
    # TODO: merge/replace with DocumentData

    def __init__(self, document_id, title, metadata, content_html):
        self.document_id = document_id
        self.title = title
        self.metadata = metadata
        self.content_html = content_html
        self.url = 'https://zoek.officielebekendmakingen.nl/{}.html'.format(document_id)

    @property
    def date_published(self):
        if self.metadata['date_published']:
            return self.metadata['date_published']
        elif self.metadata['date_submitted']:
            return self.metadata['date_submitted']
        elif self.metadata['date_received']:
            return self.metadata['date_received']
        elif self.metadata['date_available']:
            return self.metadata['date_available']
        elif self.metadata['date_letter_sent']:
            return self.metadata['date_letter_sent']
        return None


def get_document_data_mp(document_id, outputs):
    if not document_id:
        logger.error('No document id found for document_id: ' + document_id + ' - will not create document')
        return

    metadata = scraper.documents.get_metadata(document_id)

    # skip eerste kamer documents, first focus on the tweede kamer
    # TODO: handle eerste kamer documents
    if 'eerste kamer' in metadata['publisher'].lower():
        logger.info('skipping Eerste Kamer document')
        return

    document_id = metadata['overheidnl_document_id'] if metadata['overheidnl_document_id'] else document_id
    try:
        content_html = scraper.documents.get_html_content(document_id)
    except:
        logger.exception('error getting document html for document id: {}'.format(document_id))
        content_html = ''
    document_data = DocumentDataOverheidNL(
        document_id=document_id,
        title=metadata['title_full'],
        metadata=metadata,
        content_html=content_html
    )
    outputs.append(document_data)


@transaction.atomic
def create_dossier_documents(dossier, dossier_id):
    logger.info('create_dossier_documents - BEGIN')
    document_ids = scraper.documents.search_politieknl_dossier(dossier_id)

    pool = ThreadPool(processes=4)
    manager = mp.Manager()
    outputs = manager.list()
    for document_id in document_ids:
        if 'stcrt' in document_id:
            continue  # skip Staatscourant for now
        if 'ag-tk' in document_id:
            continue  # skip agenda for now
        if 'blg' in document_id:
            continue  # skip bijlage for now
        pool.apply_async(get_document_data_mp, args=(document_id, outputs))
    pool.close()
    pool.join()

    logger.info('create_dossier_documents - outputs: {}'.format(len(outputs)))

    for data in outputs:
        if 'submitter' not in data.metadata:
            data.metadata['submitter'] = 'undefined'

        dossier_for_document = dossier

        data.content_html = update_document_html_links(data.content_html)
        properties = {
            'dossier': dossier_for_document,
            'title_full': data.metadata['title_full'],
            'title_short': data.metadata['title_short'],
            'publication_type': data.metadata['publication_type'],
            'types': data.metadata['types'],
            'publisher': data.metadata['publisher'],
            'date_published': data.date_published,
            'source_url': data.url,
            'content_html': data.content_html,
        }

        document_data = DocumentData(data.document_id, data.metadata, data.content_html, data.url)
        document = DocumentFactory.create_document_and_related(document_data, properties)

        if data.metadata['is_kamerstuk']:
            is_attachement = "Bijlage" in properties['types']
            dossier_id = data.metadata.get('dossier_ids', dossier_id).split(';')[0]
            if not Kamerstuk.objects.filter(id_main=dossier_id, id_sub=data.metadata['id_sub']).exists():
                create_kamerstuk(document, dossier_id, data.title, data.metadata, is_attachement)
                category_list = get_categories(text=data.metadata['category'], category_class=CategoryDossier, sep_char='|')
                dossier_for_document.categories.add(*category_list)

        # TODO BR: enable
        # if metadata['is_agenda']:
        #     create_agenda(document, metadata)


def get_inactive_dossier_ids():
    return list(Dossier.objects.filter(status__in=[
        Dossier.VERWORPEN, Dossier.AANGENOMEN, Dossier.INGETROKKEN, Dossier.CONTROVERSIEEL
    ]).values_list('dossier_id', flat=True))


def create_wetsvoorstellen_active(skip_existing=False, max_tries=3):
    logger.info('BEGIN')
    dossiers = get_dossier_ids()
    logger.info('dossiers: {}'.format(len(dossiers)))
    dossier_ids_inactive = get_inactive_dossier_ids()
    dossier_ids_active = []
    for dossier in dossiers:
        dossier_id = Dossier.create_dossier_id(dossier.dossier_id, dossier.dossier_sub_id)
        if dossier_id not in dossier_ids_inactive:
            dossier_ids_active.append(dossier)
    dossier_ids_active.reverse()
    logger.info('dossiers active: {}'.format(dossier_ids_active))
    failed_dossiers = create_wetsvoorstellen(dossier_ids_active, skip_existing=skip_existing, max_tries=max_tries)
    logger.info('END')
    return failed_dossiers


def create_wetsvoorstellen_inactive(skip_existing=False, max_tries=3):
    logger.info('BEGIN')
    dossier_ids_inactive = get_inactive_dossier_ids()
    dossier_ids_inactive.reverse()
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
    for dossier_id in dossier_ids:
        dossier_id = Dossier.create_dossier_id(dossier_id.dossier_id, dossier_id.dossier_sub_id)
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


def get_besluiten_dossier_main(dossier_id_main, dossier_id_sub) -> List[Besluit]:
    zaken = get_zaken_dossier_main(dossier_id_main, dossier_id_sub)
    besluiten = []
    for zaak in zaken:
        besluiten += zaak.besluiten
    return besluiten


def get_besluit_last(dossier_id_main, dossier_id_sub, filter_has_votings=False) -> Besluit:
    besluiten = get_besluiten_dossier_main(dossier_id_main=dossier_id_main, dossier_id_sub=dossier_id_sub)
    last_besluit = None
    for besluit in besluiten:
        if filter_has_votings and not besluit.stemmingen:
            continue
        if besluit.agendapunt.activiteit.status == ActiviteitStatus.GEPLAND:
            # TODO: create dossier agendapunt with planned activiteit
            continue
        if last_besluit is None or besluit.agendapunt.activiteit.begin > last_besluit.agendapunt.activiteit.begin:
            last_besluit = besluit
    return last_besluit


def get_besluit_last_with_voting(dossier_id_main, dossier_id_sub) -> Besluit:
    return get_besluit_last(dossier_id_main=dossier_id_main, dossier_id_sub=dossier_id_sub, filter_has_votings=True)


def get_zaken_dossier_main(dossier_id_main, dossier_id_sub) -> List[Zaak]:
    # TODO BR: filter by Wetgeving OR Initiatiefwetgeving if tkapi makes it possible
    filter = Zaak.create_filter()
    filter.filter_kamerstukdossier(nummer=dossier_id_main, toevoeging=dossier_id_sub)
    filter.filter_soort(ZaakSoort.WETGEVING)
    zaken = Api().get_zaken(filter=filter)
    if not zaken:
        filter = Zaak.create_filter()
        filter.filter_kamerstukdossier(nummer=dossier_id_main, toevoeging=dossier_id_sub)
        filter.filter_soort(ZaakSoort.INITIATIEF_WETGEVING)
        zaken = Api().get_zaken(filter=filter)
    return zaken
