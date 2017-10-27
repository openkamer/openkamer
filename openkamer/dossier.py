import datetime
import logging
import time

from requests.exceptions import ConnectionError, ConnectTimeout, ChunkedEncodingError

from django.db import transaction

import scraper.documents
import scraper.dossiers

from document.models import CategoryDocument
from document.models import CategoryDossier
from document.models import Document
from document.models import Dossier
from document.models import Kamerstuk

from openkamer.agenda import create_agenda
from openkamer.kamerstuk import update_document_html_links
from openkamer.kamerstuk import create_submitter
from openkamer.kamerstuk import create_kamerstuk
from openkamer.voting import create_votings

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
    logger.info('BEGIN - dossier id: ' + str(dossier_id))
    Dossier.objects.filter(dossier_id=dossier_id).delete()
    dossier_url = scraper.dossiers.search_dossier_url(dossier_id)
    decision = scraper.dossiers.get_dossier_decision(dossier_url)
    dossier_new = Dossier.objects.create(
        dossier_id=dossier_id,
        url=dossier_url,
        decision=decision
    )
    search_results = scraper.documents.search_politieknl_dossier(dossier_id)
    for result in search_results:
        # skip eerste kamer documents, first focus on the tweede kamer
        # TODO: handle eerste kamer documents
        if 'eerste kamer' in result['publisher'].lower():
            logger.info('skipping Eerste Kamer document')
            continue
        # skip documents of some types and/or sources, no models implemented yet
        # TODO: handle all document types
        if 'Staatscourant' in result['type']:
            logger.info('Staatscourant, skip for now')
            continue

        document_id, content_html, title = scraper.documents.get_document_id_and_content(result['page_url'])
        if not document_id:
            logger.error('No document id found for url: ' + result['page_url'] + ' - will not create document')
            continue

        metadata = scraper.documents.get_metadata(document_id)

        if metadata['date_published']:
            date_published = metadata['date_published']
        else:
            date_published = result['date_published']

        if 'submitter' not in metadata:
            metadata['submitter'] = 'undefined'

        if 'dossier_id' in metadata:
            main_dossier_id = metadata['dossier_id'].split(';')[0].strip()
            main_dossier_id = main_dossier_id.split('-')[0]  # remove rijkswetdossier id, for example 34158-(R2048)
            if main_dossier_id != '' and str(main_dossier_id) != str(dossier_id):
                dossier_for_document, created = Dossier.objects.get_or_create(dossier_id=main_dossier_id)
            else:
                dossier_for_document = dossier_new

        content_html = update_document_html_links(content_html)

        properties = {
            'dossier': dossier_for_document,
            'title_full': metadata['title_full'],
            'title_short': metadata['title_short'],
            'publication_type': metadata['publication_type'],
            'types': metadata['types'],
            'publisher': metadata['publisher'],
            'date_published': date_published,
            'source_url': document_html_url,
            'content_html': content_html,
        }

        document, created = Document.objects.update_or_create(
            document_id=document_id,
            defaults=properties
        )

        category_list = get_categories(
            text=metadata['category'],
            category_class=CategoryDocument,
            sep_char='|'
        )
        document.categories.add(*category_list)

        submitters = metadata['submitter'].split('|')
        for submitter in submitters:
            create_submitter(document, submitter, date_published)

        if metadata['is_kamerstuk']:
            is_attachement = "Bijlage" in result['type']
            if not Kamerstuk.objects.filter(id_main=dossier_id, id_sub=metadata['id_sub']).exists():
                create_kamerstuk(document, dossier_for_document.dossier_id, title, metadata, is_attachement)
                category_list = get_categories(text=metadata['category'], category_class=CategoryDossier, sep_char='|')
                dossier_for_document.categories.add(*category_list)

        if metadata['is_agenda']:
            create_agenda(document, metadata)

    create_votings(dossier_id)
    dossier_new.set_derived_fields()
    logger.info('END - dossier id: ' + str(dossier_id))
    return dossier_new


def get_inactive_dossier_ids():
    return list(Dossier.objects.filter(status__in=[Dossier.VERWORPEN, Dossier.AANGENOMEN]).values_list('dossier_id', flat=True))


def create_wetsvoorstellen_active(skip_existing=False, max_tries=3):
    logger.info('BEGIN')
    dossier_ids = Dossier.get_dossier_ids()
    dossier_ids_inactive = get_inactive_dossier_ids()
    dossier_ids_active = []
    for dossier_id in dossier_ids:
        if dossier_id not in dossier_ids_inactive:
            dossier_ids_active.append(dossier_id)
    failed_dossiers = create_wetsvoorstellen(dossier_ids_active, skip_existing=skip_existing, max_tries=max_tries)
    logger.info('END')
    return failed_dossiers


def create_wetsvoorstellen_inactive(skip_existing=False, max_tries=3):
    logger.info('BEGIN')
    dossier_ids_inactive = get_inactive_dossier_ids()
    failed_dossiers = create_wetsvoorstellen(dossier_ids_inactive, skip_existing=skip_existing, max_tries=max_tries)
    logger.info('END')
    return failed_dossiers


def create_wetsvoorstellen_all(skip_existing=False, max_tries=3):
    logger.info('BEGIN')
    dossier_ids = Dossier.get_dossier_ids()
    failed_dossiers = create_wetsvoorstellen(dossier_ids, skip_existing=skip_existing, max_tries=max_tries)
    logger.info('END')
    return failed_dossiers


def create_wetsvoorstellen(dossier_ids, skip_existing=False, max_tries=3):
    logger.info('BEGIN')
    failed_dossiers = []
    for dossier_id in dossier_ids:
        dossiers = Dossier.objects.filter(dossier_id=dossier_id)
        if skip_existing and dossiers.exists():
            logger.info('dossier already exists, skip')
            continue
        try:
            create_dossier_retry_on_error(dossier_id=dossier_id, max_tries=max_tries)
        except Exception as error:
            failed_dossiers.append(dossier_id)
            logger.error('error for dossier id: ' + str(dossier_id))
            logger.error(error)
    logger.info('END')
    return failed_dossiers


@transaction.atomic
def get_categories(text, category_class=CategoryDocument, sep_char='|'):
    category_list = text.split(sep_char)
    categories = []
    for category_name in category_list:
        name = category_name.lower().strip()
        if name:
            category, created = category_class.objects.get_or_create(name=name)
            categories.append(category)
    return categories
