import logging
import re
import lxml

from django.db import transaction

from document.models import Kamervraag
from document.models import Kamerantwoord
from document.models import Antwoord
from document.models import Vraag
from document.models import CategoryDocument

from document.models import Document

import website.create
import scraper.documents

logger = logging.getLogger(__name__)


def get_kamervraag_metadata(kamervraag_info):
    metadata = scraper.documents.get_metadata(kamervraag_info['overheidnl_document_id'])
    return metadata


# @transaction.atomic
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
    kamervraag = Kamervraag.objects.create(document=document, vraagnummer=vraagnummer)
    create_vragen_from_kamervraag_html(kamervraag)


@transaction.atomic
def create_kamervraag_document(kamervraag_info):
    print('BEGIN')
    print(kamervraag_info['document_url'])
    document_html_url = kamervraag_info['document_url'] + '.html'
    document_id, content_html, title = scraper.documents.get_kamervraag_document_id_and_content(document_html_url)
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
        logger.warning('document with id: ' + document_id + ' already exists, recreate document.')

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


# @transaction.atomic
def create_antwoorden(year, max_n=None):
    infos = Kamerantwoord.get_antwoorden_info(year)
    counter = 0
    for info in infos:
        create_kamerantwoord(info)
        if max_n and counter >= max_n:
            break
        counter += 1


@transaction.atomic
def find_kamerantwoorden():
    logger.info('BEGIN')
    kamerantwoorden = Kamerantwoord.objects.all()
    for kamerantwoord in kamerantwoorden:
        kamervragen = Kamervraag.objects.filter(vraagnummer=kamerantwoord.vraagnummer)
        if kamervragen:
            logger.info('vraag found!!!')
            kamervraag = kamervragen[0]
            kamervraag.kamerantwoord = kamerantwoord
            kamervraag.save()
    logger.info('END')


@transaction.atomic
def create_kamerantwoord(kamervraag_info):
    document, vraagnummer = create_kamervraag_document(kamervraag_info)
    Kamerantwoord.objects.filter(document=document).delete()
    kamerantwoord = Kamerantwoord.objects.create(document=document, vraagnummer=vraagnummer)
    create_antwoorden_from_antwoord_html(kamerantwoord)


@transaction.atomic
def create_vragen_from_kamervraag_html(kamervraag):
    logger.info('BEGIN')
    Vraag.objects.filter(kamervraag=kamervraag).delete()
    tree = lxml.html.fromstring(kamervraag.document.content_html)
    elements = tree.xpath('//div[@class="vraag"]/p')
    counter = 1
    for element in elements:
        if element.text == '':
            logger.warning('empty vraag text found for kamervraag ' + str(kamervraag.document.document_url) + 'vraag nr: ' + str(counter))
            continue
        Vraag.objects.create(nr=counter, kamervraag=kamervraag, text=element.text)
        counter += 1
    logger.info('END: ' + str(counter) + ' vragen found')


@transaction.atomic
def create_antwoorden_from_antwoord_html(kamerantwoord):
    logger.info('BEGIN')
    Antwoord.objects.filter(kamerantwoord=kamerantwoord).delete()
    tree = lxml.html.fromstring(kamerantwoord.document.content_html)
    elements = tree.xpath('//div[@class="antwoord"]')
    counter = 1
    antwoorden = []
    for element in elements:
        answer_text = ''
        for paragraph in element.iter('p'):
            if paragraph.text is None or paragraph.text == '':
                logger.warning('empty vraag text found for antwoord ' + str(kamerantwoord.document.document_url) + 'vraag nr: ' + str(counter))
            else:
                answer_text += paragraph.text + '\n'
        antwoord = Antwoord.objects.create(nr=counter, kamerantwoord=kamerantwoord, text=answer_text)
        antwoorden.append(antwoord)
        # logger.info(answer_text)
        counter += 1
    # logger.info(antwoorden)
    logger.info('END: ' + str(counter) + ' vragen found')