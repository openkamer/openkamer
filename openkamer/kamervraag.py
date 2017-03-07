import logging
import re

from django.db import transaction

from document.models import Kamervraag
from document.models import Antwoord
from document.models import CategoryDocument

from document.models import Document

import website.create
import scraper.documents

logger = logging.getLogger(__name__)


def get_kamervraag_metadata(kamervraag_info):
    metadata = scraper.documents.get_metadata(kamervraag_info['overheidnl_document_id'])
    return metadata


@transaction.atomic
def create_kamervragen(year, max_n):
    infos = Kamervraag.get_kamervragen_info(year)
    counter = 0
    for info in infos:
        create_kamervraag(info)
        if max_n and counter >= max_n:
            return
        counter += 1


@transaction.atomic
def create_kamervraag(kamervraag_info):
    document, vraagnummer = create_kamervraag_document(kamervraag_info)
    Kamervraag.objects.filter(document=document).delete()
    Kamervraag.objects.create(document=document, vraagnummer=vraagnummer)


@transaction.atomic
def create_kamervraag_document(kamervraag_info):
    print('BEGIN')
    print(kamervraag_info['document_url'])
    document_html_url = kamervraag_info['document_url'] + '.html'
    document_id, content_html, title = scraper.documents.get_kamervraag_document_id_and_content(document_html_url)
    print(document_id)
    # print(content_html)
    print('title: ' + title)
    metadata = get_kamervraag_metadata(kamervraag_info)
    document_id = kamervraag_info['document_number']

    if metadata['date_published']:
        date_published = metadata['date_published']
    elif metadata['date_submitted']:
        date_published = metadata['date_submitted']
    else:
        date_published = None

    if 'submitter' not in metadata:
        metadata['submitter'] = 'undefined'

    documents = Document.objects.filter(document_id=document_id).delete()
    if documents:
        logger.warning('document with id: ' + document_id + ' already exists, skip creating document.')

    content_html = website.create.update_document_html_links(content_html)

    document = Document.objects.create(
        dossier=None,
        document_id=document_id,
        title_full=title,
        title_short=metadata['title_short'],
        publication_type=metadata['publication_type'],
        publisher=metadata['publisher'],
        date_published=date_published,
        source_url=document_html_url,
        content_html=content_html,
    )
    category_list = website.create.get_categories(text=metadata['category'], category_class=CategoryDocument, sep_char='|')
    document.categories.add(*category_list)

    submitters = metadata['submitter'].split('|')
    for submitter in submitters:
        print(submitter)
        website.create.create_submitter(document, submitter, date_published)

    print('END')
    return document, metadata['vraagnummer']


def get_antwoord_metadata(antwoord_info):
    metadata = scraper.documents.get_metadata(antwoord_info['overheidnl_document_id'])
    return metadata


@transaction.atomic
def create_antwoorden(year, max_n=None):
    infos = Antwoord.get_antwoorden_info(year)
    counter = 0
    for info in infos:
        create_antwoord(info)
        if max_n and counter >= max_n:
            break
        counter += 1
    find_kamervragen()


@transaction.atomic
def find_kamervragen():
    logger.info('BEGIN')
    antwoorden = Antwoord.objects.all()
    for antwoord in antwoorden:
        vragen = Kamervraag.objects.filter(vraagnummer=antwoord.vraagnummer)
        if vragen:
            logger.info('vraag found!!!')
            antwoord.kamervraag = vragen[0]
            antwoord.save()
    logger.info('END')


@transaction.atomic
def create_antwoord(kamervraag_info):
    document, vraagnummer = create_kamervraag_document(kamervraag_info)
    Antwoord.objects.filter(document=document).delete()
    Antwoord.objects.create(document=document, vraagnummer=vraagnummer)