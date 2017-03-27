import logging
import scraper.documents

from document.models import Document
from document.models import CategoryDocument

import website.create

logger = logging.getLogger(__name__)


def create_document(overheidnl_document_id, document_id=None, dossier_id=None):
    logger.info('BEGIN')
    document_html_url = 'https://zoek.officielebekendmakingen.nl/' + overheidnl_document_id + '.html'
    document_id_overheid, content_html, title = scraper.documents.get_kamervraag_document_id_and_content(document_html_url)
    content_html = website.create.update_document_html_links(content_html)

    metadata = scraper.documents.get_metadata(overheidnl_document_id)
    if document_id is None:
        document_id = overheidnl_document_id

    if metadata['date_published']:
        date_published = metadata['date_published']
    elif metadata['date_submitted']:
        date_published = metadata['date_submitted']
    else:
        date_published = None

    if 'submitter' not in metadata:
        metadata['submitter'] = 'undefined'
    if metadata['receiver']:
        metadata['submitter'] = metadata['receiver']

    documents = Document.objects.filter(document_id=document_id)
    if documents:
        documents.delete()
        logger.warning('document with id: ' + document_id + ' already exists, recreate document.')

    document = Document.objects.create(
        dossier=None,
        document_id=document_id,
        title_full=metadata['title_full'],
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
        website.create.create_submitter(document, submitter, date_published)

    logger.info('END')
    return document
