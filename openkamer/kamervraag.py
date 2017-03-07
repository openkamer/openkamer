import logging

from django.db import transaction

from document.models import Kamervraag

from document.models import Document

import website.create
import scraper.documents

logger = logging.getLogger(__name__)


def get_kamervraag_metadata(kamervraag_info):
    infos = Kamervraag.get_kamervragen_info(2016)
    kamervraag_info = infos[0]
    metadata = scraper.documents.get_metadata(kamervraag_info['overheidnl_document_id'])
    return metadata

@transaction.atomic
def create_kamervragen(year):
    infos = Kamervraag.get_kamervragen_info(year)
    for info in infos:
        create_kamervraag(info)


@transaction.atomic
def create_kamervraag(kamervraag_info):
    document = create_kamervraag_document(kamervraag_info)
    Kamervraag.objects.filter(document=document).delete()
    Kamervraag.objects.create(document=document)


@transaction.atomic
def create_kamervraag_document(kamervraag_info):
    print('BEGIN')
    print(kamervraag_info['document_url'])
    document_id, content_html, title = scraper.documents.get_kamervraag_document_id_and_content(kamervraag_info['document_url'] + '.html')
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
        content_html=content_html,
    )
    print('END')
    return document
