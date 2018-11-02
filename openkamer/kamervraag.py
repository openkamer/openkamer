import logging
import re
import lxml

from django.db import transaction

from document.models import Kamervraag
from document.models import Kamerantwoord
from document.models import KamervraagMededeling
from document.models import Antwoord
from document.models import Vraag
from document.models import FootNote

from openkamer.document import DocumentFactory

logger = logging.getLogger(__name__)


def create_kamervragen(year, max_n=None, skip_if_exists=False):
    logger.info('BEGIN')
    infos = Kamervraag.get_kamervragen_info(year)
    counter = 1
    kamervragen = []
    kamerantwoorden = []
    for info in infos:
        try:
            kamervraag, related_document_overheid_ids = create_kamervraag(info['overheidnl_document_id'], skip_if_exists=skip_if_exists)
            if kamervraag is not None:
                kamervragen.append(kamervraag)
                kamerantwoord, mededelingen = create_related_kamervraag_documents(kamervraag, related_document_overheid_ids)
                if kamerantwoord:
                    kamerantwoorden.append(kamerantwoord)
        except Exception as error:
            logger.error('error for kamervraag id: ' + str(info['overheidnl_document_id']))
            logger.exception(error)
        if max_n and counter >= max_n:
            return kamervragen, kamerantwoorden
        counter += 1
    logger.info('END')
    return kamervragen, kamerantwoorden


def create_related_kamervraag_documents(kamervraag, overheid_document_ids):
    kamerantwoord = None
    mededelingen = []
    for overheid_document_id in overheid_document_ids:
        kamerantwoord, mededeling = create_kamerantwoord(overheid_document_id)
        if kamerantwoord:
            kamervraag.kamerantwoord = kamerantwoord
            kamervraag.save()
        if mededeling:
            mededeling.kamervraag = kamervraag
            mededeling.save()
            mededelingen.append(mededeling)
    return kamerantwoord, mededelingen


def create_antwoorden(year, max_n=None, skip_if_exists=False):
    logger.info('BEGIN')
    infos = Kamerantwoord.get_antwoorden_info(year)
    counter = 1
    for info in infos:
        logger.info(info['overheidnl_document_id'])
        try:
            create_kamerantwoord(info['overheidnl_document_id'], skip_if_exists=skip_if_exists)
        except Exception as error:
            logger.error('error for kamerantwoord id: ' + str(info['overheidnl_document_id']))
            logger.exception(error)
        if max_n and counter >= max_n:
            break
        counter += 1
    logger.info('END')


def get_or_create_kamervraag(vraagnummer, document):
    kamervragen = Kamervraag.objects.filter(vraagnummer=vraagnummer)
    if kamervragen.count() == 1:
        kamervraag = kamervragen[0]
    else:
        kamervragen.delete()
        kamervraag = Kamervraag()
    kamervraag.document = document
    kamervraag.vraagnummer = vraagnummer
    kamervraag.receiver = get_receiver_from_title(document.title_full)
    kamervraag.save()
    return kamervraag


def get_or_create_kamerantwoord(vraagnummer, document):
    kamerantwoorden = Kamerantwoord.objects.filter(vraagnummer=vraagnummer)
    if kamerantwoorden.count() == 1:
        kamerantwoord = kamerantwoorden[0]
    else:
        kamerantwoorden.delete()
        kamerantwoord = Kamerantwoord()
    kamerantwoord.document = document
    kamerantwoord.vraagnummer = vraagnummer
    kamerantwoord.save()
    return kamerantwoord


@transaction.atomic
def create_kamervraag(overheidnl_document_id, skip_if_exists=False):
    if skip_if_exists and Kamervraag.objects.filter(document__document_id=overheidnl_document_id).exists():
        return None, []
    document_factory = DocumentFactory(DocumentFactory.DocumentType.KAMERVRAAG)
    document, related_document_ids, vraagnummer = document_factory.create_kamervraag_document(overheidnl_document_id)
    kamervraag = get_or_create_kamervraag(vraagnummer, document)
    create_vragen_from_kamervraag_html(kamervraag)
    footnotes = create_footnotes(kamervraag.document.content_html)
    FootNote.objects.filter(document=document).delete()
    for footnote in footnotes:
        FootNote.objects.create(document=document, nr=footnote['nr'], text=footnote['text'], url=footnote['url'])
    return kamervraag, related_document_ids


@transaction.atomic
def create_kamerantwoord(overheidnl_document_id, skip_if_exists=False):
    if skip_if_exists and Kamerantwoord.objects.filter(document__document_id=overheidnl_document_id).exists():
        return None
    document_factory = DocumentFactory(DocumentFactory.DocumentType.KAMERVRAAG)
    document, related_document_ids, vraagnummer = document_factory.create_kamervraag_document(overheidnl_document_id)
    if 'mededeling' in document.types.lower():
        KamervraagMededeling.objects.filter(vraagnummer=vraagnummer).delete()
        mededeling = KamervraagMededeling.objects.create(document=document, vraagnummer=vraagnummer)
        create_kamervraag_mededeling_from_html(mededeling)
        kamerantwoord = None
    else:
        kamerantwoord = get_or_create_kamerantwoord(vraagnummer, document)
        create_antwoorden_from_antwoord_html(kamerantwoord)
        mededeling = None
    return kamerantwoord, mededeling


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
                with transaction.atomic():
                    kamervraag.kamerantwoord = kamerantwoord
                    kamervraag.save()
            except IntegrityError as error:
                logger.error('kamervraag: ' + str(kamervraag.id))
                logger.error('kamerantwoord: ' + str(kamerantwoord.id))
                logger.exception(error)

    mededelingen = KamervraagMededeling.objects.all()
    for mededeling in mededelingen:
        kamervragen = Kamervraag.objects.filter(vraagnummer=mededeling.vraagnummer)
        if kamervragen:
            kamervraag = kamervragen[0]
            try:
                with transaction.atomic():
                    mededeling.kamervraag = kamervraag
                    mededeling.save()
            except IntegrityError as error:
                logger.error('mededeling: ' + str(mededeling.id))
                logger.error('kamervraag: ' + str(kamervraag.id))
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
                logger.warning('empty vraag text found for antwoord ' + str(kamervraag.document.document_url) + 'vraag nr: ' + str(counter))
            else:
                vraag_text += paragraph.text_content() + '\n'
        vraag_text = re.sub('\s{2,}', ' ', vraag_text).strip()
        Vraag.objects.create(nr=counter, kamervraag=kamervraag, text=vraag_text)
        counter += 1
    logger.info('END: ' + str(counter) + ' vragen found')


@transaction.atomic
def create_kamervraag_mededeling_from_html(mededeling):
    tree = lxml.html.fromstring(mededeling.document.content_html)
    elements = tree.xpath('//div[@class="kamervraagopmerking"]')
    text = ''
    for paragraph in elements[0].iter('p'):
        if paragraph.text is None or paragraph.text == '':
            logger.warning('empty mededeling text found for antwoord ' + str(mededeling.document.document_url))
        else:
            text += re.sub('\s{2,}', ' ', paragraph.text_content()).strip()
            text += '\n'
    mededeling.text = text
    mededeling.save()
    logger.info('END')


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
        if element.xpath('h2'):
            vraag_numbers = element.xpath('h2')  # <h2>Vraag 1</h2> or <h2>Vraag 2, 3</h2>
        else:
            vraag_numbers = element.xpath('p[@class="nummer"]')   # <p class="nummer">1</p>
        vraag_numbers = vraag_numbers[0].text_content().strip()
        result = re.findall('(\D*)\d', vraag_numbers)
        if result:
            vraag_numbers = vraag_numbers.replace(result[0], '')
        vraag_numbers = vraag_numbers.replace('en', ',').replace(' ', '').split(',')
        for paragraph in element.iter('p'):
            if paragraph.text is None or paragraph.text == '':
                logger.warning('empty vraag text found for antwoord ' + str(kamerantwoord.document.document_url) + ' antwoord nr: ' + str(counter))
            else:
                answer_text += re.sub('\s{2,}', ' ', paragraph.text_content()).strip()
                answer_text += '\n'
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
