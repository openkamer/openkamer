import logging
import re
import lxml

from django.db import transaction

from document.models import Kamervraag
from document.models import Kamerantwoord
from document.models import Antwoord
from document.models import Vraag
from document.models import CategoryDocument
from document.models import FootNote

from document.models import Document

import website.create
import scraper.documents

logger = logging.getLogger(__name__)


def create_kamervragen(year, max_n=None, skip_if_exists=False):
    logger.info('BEGIN')
    infos = Kamervraag.get_kamervragen_info(year)
    counter = 0
    for info in infos:
        try:
            create_kamervraag(info['document_number'], info['overheidnl_document_id'], skip_if_exists=skip_if_exists)
        except Exception as error:
            logger.error('error for kamervraag id: ' + str(info['overheidnl_document_id']))
            logger.exception(error)
        if max_n and counter >= max_n:
            return
        counter += 1
    logger.info('END')


def create_antwoorden(year, max_n=None, skip_if_exists=False):
    logger.info('BEGIN')
    infos = Kamerantwoord.get_antwoorden_info(year)
    counter = 0
    for info in infos:
        try:
            create_kamerantwoord(info['document_number'], info['overheidnl_document_id'], skip_if_exists=skip_if_exists)
        except Exception as error:
            logger.error('error for kamerantwoord id: ' + str(info['overheidnl_document_id']))
            logger.exception(error)
        if max_n and counter >= max_n:
            break
        counter += 1
    logger.info('END')


@transaction.atomic
def create_kamervraag(document_number, overheidnl_document_id, skip_if_exists=False):
    if skip_if_exists and Kamervraag.objects.filter(document__document_id=document_number).exists():
        return
    document, vraagnummer = create_kamervraag_document(document_number, overheidnl_document_id)
    Kamervraag.objects.filter(document=document).delete()
    kamervraag = Kamervraag.objects.create(
        document=document,
        vraagnummer=vraagnummer,
        receiver=get_receiver_from_title(document.title_full)
    )
    create_vragen_from_kamervraag_html(kamervraag)
    footnotes = create_footnotes(kamervraag.document.content_html)
    for footnote in footnotes:
        FootNote.objects.create(document=document, nr=footnote['nr'], text=footnote['text'], url=footnote['url'])
    return kamervraag


@transaction.atomic
def create_kamerantwoord(document_number, overheidnl_document_id, skip_if_exists=False):
    if skip_if_exists and Kamerantwoord.objects.filter(document__document_id=document_number).exists():
        return
    document, vraagnummer = create_kamervraag_document(document_number, overheidnl_document_id)
    Kamerantwoord.objects.filter(document=document).delete()
    kamerantwoord = Kamerantwoord.objects.create(document=document, vraagnummer=vraagnummer)
    create_antwoorden_from_antwoord_html(kamerantwoord)
    return kamerantwoord


@transaction.atomic
def create_kamervraag_document(document_number, overheidnl_document_id):
    logger.info('BEGIN')
    document_html_url = 'https://zoek.officielebekendmakingen.nl/' + str(overheidnl_document_id) +'.html'
    logger.info(document_html_url)
    document_id, content_html, title = scraper.documents.get_kamervraag_document_id_and_content(document_html_url)
    metadata = scraper.documents.get_metadata(overheidnl_document_id)
    document_id = document_number

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

    documents = Document.objects.filter(document_id=document_id).delete()
    if documents:
        logger.warning('document with id: ' + document_id + ' already exists, recreate document.')

    content_html = website.create.update_document_html_links(content_html)

    document = Document.objects.create(
        dossier=None,
        document_id=document_id,
        title_full=title,
        title_short=metadata['title_full'],
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
    return document, metadata['vraagnummer']


def get_receiver_from_title(title_full):
    pattern = 'Vragen\s.*aan de\s(.*) over\s.*'
    result = re.findall(pattern, title_full)
    if result:
        return result[0]
    return ''


@transaction.atomic
def link_kamervragen_and_antwoorden():
    logger.info('BEGIN')
    from django.db.utils import IntegrityError
    kamerantwoorden = Kamerantwoord.objects.all()
    for kamerantwoord in kamerantwoorden:
        kamervragen = Kamervraag.objects.filter(vraagnummer=kamerantwoord.vraagnummer)
        if kamervragen:
            kamervraag = kamervragen[0]
            try:
                kamervraag.kamerantwoord = kamerantwoord
                kamervraag.save()
            except IntegrityError as error:
                logger.error('kamervraag: ' + str(kamervraag))
                logger.error('kamerantwoord: ' + str(kamerantwoord.id))
                logger.exception(error)
    logger.info('END')


@transaction.atomic
def create_vragen_from_kamervraag_html(kamervraag):
    logger.info('BEGIN')
    Vraag.objects.filter(kamervraag=kamervraag).delete()
    tree = lxml.html.fromstring(kamervraag.document.content_html)
    elements = tree.xpath('//div[@class="vraag"]')
    counter = 1
    for element in elements:
        vraag_text = ''
        for paragraph in element.iter('p'):
            if paragraph.text is None or paragraph.text == '':
                logger.warning('empty vraag text found for antwoord ' + str(kamervraag.document.document_url) + 'vraat nr: ' + str(counter))
            else:
                vraag_text += paragraph.text_content() + '\n'
        vraag_text = re.sub('\s{2,}', ' ', vraag_text).strip()
        Vraag.objects.create(nr=counter, kamervraag=kamervraag, text=vraag_text)
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
        vraag_numbers = element.xpath('h2')[0].text_content().strip()  # <h2>Vraag 1</h2> or <h2>Vraag 2, 3</h2>
        result = re.findall('(\D*)\d', vraag_numbers)
        if result:
            vraag_numbers = vraag_numbers.replace(result[0], '')
        vraag_numbers = vraag_numbers.replace('en', ',').replace(' ', '').split(',')
        for paragraph in element.iter('p'):
            if paragraph.text is None or paragraph.text == '':
                logger.warning('empty vraag text found for antwoord ' + str(kamerantwoord.document.document_url) + 'antwoord nr: ' + str(counter))
            else:
                answer_text += paragraph.text_content() + '\n'
        answer_text = re.sub('\s{2,}', ' ', answer_text).strip()
        counter = 0
        see_answer_nr = None
        for number in vraag_numbers:
            try:
                first_number = int(vraag_numbers[0])
                number = int(number)
            except ValueError:
                logger.info(vraag_numbers)
                logger.error('could not convert antwoord number to integer: ' + number + ' for document: ' + str(kamerantwoord.document.document_url))
                continue
            if counter > 0:
                answer_text = 'Zie antwoord vraag ' + str(vraag_numbers[0] + '.')
                see_answer_nr = first_number
            antwoord = Antwoord.objects.create(nr=number, kamerantwoord=kamerantwoord, text=answer_text, see_answer_nr=see_answer_nr)
            antwoorden.append(antwoord)
            counter += 1
    logger.info('END')


def create_footnotes(footnotes_html):
    footnotes = []
    tree = lxml.html.fromstring(footnotes_html)
    elements = tree.xpath('//div[contains(@class, "voet noot")]')
    for element in elements:
        text = element.xpath('p')[0].text_content()
        note_numbers = element.xpath('.//span[@class="nootnum"]')
        if note_numbers:
            nr = note_numbers[0].text_content()
        else:
            nr = None
        links = element.xpath('p/a')
        if links:
            url = links[0].get('href')
        else:
            url = ''
        footnote = {
            'nr': nr,
            'text': text,
            'url': url
        }
        footnotes.append(footnote)
    return footnotes
