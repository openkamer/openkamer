import logging
import re
import lxml
import datetime
from typing import List

from django.db import transaction

import tkapi
import tkapi.kamervraag
from tkapi.document import Document as TKDocument
from tkapi.util.document import get_overheidnl_id
import tkapi.zaak
from tkapi.document import DocumentSoort

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
    year = int(year)
    month = 1
    begin_datetime = datetime.datetime(year=year, month=month, day=1)
    end_datetime = datetime.datetime(year=year+1, month=month, day=1)
    tk_zaken = get_tk_kamervraag_zaken(begin_datetime, end_datetime)

    counter = 1
    kamervragen = []
    kamerantwoorden = []
    for tk_zaak in tk_zaken:
        try:
            kamervraag, kamerantwoord = create_for_zaak(tk_zaak, skip_if_exists)
            kamervragen.append(kamervraag)
            kamerantwoorden.append(kamerantwoord)
        except Exception as error:
            logger.error('error for kamervraag zaak nummber: {}'.format(tk_zaak.nummer))
            logger.exception(error)
        if max_n and counter >= max_n:
            return kamervragen, kamerantwoorden
        counter += 1
    logger.info('END')
    return kamervragen, kamerantwoorden


@transaction.atomic
def create_for_zaak(tk_zaak: tkapi.zaak.Zaak, skip_if_exists=False):
    logger.info('BEGIN: {}'.format(tk_zaak.nummer))
    kamervraag = None
    kamerantwoord = None
    mededelingen = []

    for tk_doc in tk_zaak.documenten:
        if tk_doc.soort == DocumentSoort.SCHRIFTELIJKE_VRAGEN:
            overheid_id = get_overheidnl_id(tk_doc)
            kamervraag = create_kamervraag(tk_doc, overheid_id, skip_if_exists=skip_if_exists)
        elif tk_doc.soort == DocumentSoort.ANTWOORD_SCHRIFTELIJKE_VRAGEN:
            overheid_id = get_overheidnl_id(tk_doc)
            kamerantwoord = create_kamerantwoord(tk_doc, overheid_id, skip_if_exists=skip_if_exists)
        elif tk_doc.soort == DocumentSoort.MEDEDELING_UITSTEL_ANTWOORD:
            overheid_id = get_overheidnl_id(tk_doc)
            mededeling = create_mededeling(tk_doc, overheid_id)
            mededelingen.append(mededeling)

    if kamerantwoord:
        kamervraag.kamerantwoord = kamerantwoord
        kamervraag.save()
    for mededeling in mededelingen:
        mededeling.kamervraag = kamervraag
        mededeling.save()
    logger.info('END: {}'.format(tk_zaak.nummer))
    return kamervraag, kamerantwoord


def get_tk_kamervraag_zaken(begin_datetime, end_datetime) -> List[tkapi.zaak.Zaak]:
    filter = tkapi.zaak.Zaak.create_filter()
    filter.filter_date_range(begin_datetime, end_datetime)
    filter.filter_soort(tkapi.zaak.ZaakSoort.SCHRIFTELIJKE_VRAGEN)
    zaken = tkapi.TKApi.get_zaken(filter=filter)
    return zaken


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
def create_kamervraag(tk_document: TKDocument, overheidnl_document_id, skip_if_exists=False):
    if skip_if_exists and Kamervraag.objects.filter(document__document_id=overheidnl_document_id).exists():
        return Kamervraag.objects.filter(document__document_id=overheidnl_document_id)[0]
    document_factory = DocumentFactory()
    document, vraagnummer = document_factory.create_kamervraag_document(tk_document, overheidnl_document_id)
    kamervraag = get_or_create_kamervraag(vraagnummer, document)
    create_vragen_from_kamervraag_html(kamervraag)
    footnotes = create_footnotes(kamervraag.document.content_html)
    FootNote.objects.filter(document=document).delete()
    for footnote in footnotes:
        FootNote.objects.create(document=document, nr=footnote['nr'], text=footnote['text'], url=footnote['url'])
    return kamervraag


@transaction.atomic
def create_kamerantwoord(tk_document: TKDocument, overheidnl_document_id, skip_if_exists=False):
    if skip_if_exists and Kamerantwoord.objects.filter(document__document_id=overheidnl_document_id).exists():
        return Kamerantwoord.objects.filter(document__document_id=overheidnl_document_id)[0]
    document_factory = DocumentFactory()
    document, vraagnummer = document_factory.create_kamervraag_document(tk_document, overheidnl_document_id)
    kamerantwoord = get_or_create_kamerantwoord(vraagnummer, document)
    create_antwoorden_from_antwoord_html(kamerantwoord)
    return kamerantwoord


@transaction.atomic
def create_mededeling(tk_document: TKDocument, overheidnl_document_id):
    document_factory = DocumentFactory()
    document, vraagnummer = document_factory.create_kamervraag_document(tk_document, overheidnl_document_id)
    KamervraagMededeling.objects.filter(vraagnummer=vraagnummer).delete()
    mededeling = KamervraagMededeling.objects.create(document=document, vraagnummer=vraagnummer)
    create_kamervraag_mededeling_from_html(mededeling)
    return mededeling


def get_receiver_from_title(title_full):
    pattern = 'Vragen\s.*aan de\s(.*) over\s.*'
    result = re.findall(pattern, title_full)
    if result:
        return result[0]
    return ''


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
