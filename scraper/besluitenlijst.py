import datetime
import logging
import re
from io import StringIO

import lxml
import dateparser
import requests

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

logger = logging.getLogger(__name__)

# TODO: compile regex in this module to improve performance


def get_voortouwcommissies_besluiten_urls():
    logger.info('BEGIN')
    url = 'https://www.tweedekamer.nl/kamerstukken/besluitenlijsten'
    commissions = []
    page = requests.get(url)
    tree = lxml.html.fromstring(page.content)
    elements = tree.xpath('//div[@class="filter-container"]/ul/li/a')
    elements += tree.xpath('//div[@class="filter-container"]/div[@class="readmore"]/ul/li/a')
    for element in elements:
        if 'Besluitenlijsten' in element.attrib['href']:
            commission = {
                'name': re.findall("(.*)\(\d+\)", element.text)[0].strip(),
                'url': url + element.attrib['href']
            }
            logger.info('commision url added for: ' + commission['name'])
            commissions.append(commission)
    logger.info('END')
    return commissions


def get_besluitenlijsten_urls(overview_url, max_results=None, ignore_agendas=True):
    logger.info('BEGIN')
    logger.info('url ' + overview_url)
    ulrs = []
    new_url_found = True
    start = 1
    while new_url_found:
        logger.info('start at: ' + str(start))
        url = overview_url + '&sta=' + str(start)
        page = requests.get(url)
        tree = lxml.html.fromstring(page.content)
        elements = tree.xpath('//ul[@class="decisionlist"]/li/a')
        new_url_found = len(elements) != 0
        for element in elements:
            is_agenda_document = False
            for span in element.iter('span'):
                if 'class' not in span.attrib:
                    title = span.text.strip()
                    if 'agenda' in title.lower():
                        is_agenda_document = True
                        break
            start += 1
            pdf_url = 'https://www.tweedekamer.nl' + element.attrib['href']
            if not (ignore_agendas and is_agenda_document):
                logger.info(pdf_url)
                ulrs.append(pdf_url)
            else:
                logger.info('ignoring besluitenlijst agenda')
            if max_results and len(ulrs) >= max_results:
                return ulrs
    logger.info('END')
    return ulrs


class BesluitenLijst(object):
    def __init__(self, text):
        self.text = text
        self.title = self.get_title(text)
        self.voortouwcommissie = self.get_voortouwcommissie(text)
        self.activiteitnummer = self.get_activiteitnummer(text)
        self.date_published = self.get_date_published(text)
        self.items = create_besluit_items(text)
        self.url = ''

    def __str__(self):
        return self.title + '\n' + self.voortouwcommissie + '\n' + self.activiteitnummer + '\n' + str(self.date_published)

    @staticmethod
    def get_title(text):
        end_line_pattern = '\d{1,2}\s\w+\s\d{4}'
        pattern = 'Document:\s{0,}([\w\s]+' + end_line_pattern + ')'
        title = BesluitenLijst.find_first(pattern, text)
        if not title:
            pattern = 'Document:\s{0,}(.*)'
            title = BesluitenLijst.find_first(pattern, text)
        if not title:
            pattern = 'Onderwerp:\s{0,}(.*)'
            title = BesluitenLijst.find_first(pattern, text)
        return title.strip()

    @staticmethod
    def get_voortouwcommissie(text):
        pattern = 'Voortouwcommissie:\s{0,}(.*)'
        return BesluitenLijst.find_first(pattern, text)

    @staticmethod
    def get_activiteitnummer(text):
        pattern = 'Activiteitnummer:\s{0,}(.*)'
        return BesluitenLijst.find_first(pattern, text)

    @staticmethod
    def get_date_published(text):
        pattern = '\d{1,2}\s\w+\s\d{4}'
        result = re.findall(pattern, text)[0]  # first date is publication date
        date_published = dateparser.parse(result).date()
        return date_published

    @staticmethod
    def find_first(pattern, text):
        result = re.findall(pattern, text)
        if result:
            return result[0].strip()
        return ''


class BesluitItem(object):
    def __init__(self):
        self.title = ''
        self.cases = []

    def print(self):
        print('Agendapunt: ' + self.title)
        for case in self.cases:
            print('------------')
            case.print()


class BesluitItemCase(object):
    def __init__(self, title):
        self.title = title
        self.related_document_ids = self.get_related_document_ids(title)
        self.decisions = []
        self.notes = []
        self.extra = ''
        self.volgcommissies = []

    @staticmethod
    def create_str_list(list_data, sep_char='|'):
        str = ''
        for index, decision in enumerate(list_data):
            str += decision
            if index < (len(list_data)-1):
                str += sep_char
        return str

    @staticmethod
    def get_related_document_ids(text):
        pattern = "[0-9]{5}-[0-9]{1,2}"
        document_ids = re.findall(pattern, text)
        return document_ids

    def print(self):
        print('Zaak: ' + self.title)
        print('decisions:')
        print(self.decisions)
        print('notes:')
        print(self.notes)
        print('volgcommissies:')
        print(self.volgcommissies)
        print('related documents:')
        print(self.related_document_ids)


def create_besluit_items(text):
    punten = find_agendapunten(text)
    besluit_items = []
    for punt in punten:
        besluit = BesluitItem()
        besluit.title = punt['title']
        besluit_text = text[punt['start']:punt['end']]
        cases = find_cases(besluit_text)
        for case in cases:
            item_case = BesluitItemCase(case['title'])
            case_text = besluit_text[case['start']:case['end']]
            decisions = find_decisions(case_text)
            for decision in decisions:
                item_case.decisions.append(decision['title'])
            notes = find_notes(case_text)
            for note in notes:
                item_case.notes.append(note['title'])
            volgcommissies = find_volgcommissies(case_text)
            for volgcommissie in volgcommissies:
                item_case.volgcommissies.append(volgcommissie['title'])
            besluit.cases.append(item_case)
        # besluit.print()
        besluit_items.append(besluit)
    return besluit_items


def besluitenlijst_pdf_to_text(filepath):
    text = pdf_to_text(filepath)
    text = format_text(text)
    # with open('data/lijst.txt', 'w') as fileout:
    #     fileout.write(text)
    return text


def create_besluitenlijst(text):
    obj = BesluitenLijst(text)
    return obj


def find_agendapunten(text):
    pattern = "Agendapunt:(.*)"
    return find_items(pattern, text)


def find_cases(text):
    pattern = "Zaak:(.*)"
    return find_items(pattern, text)


def find_decisions(text):
    pattern = "Besluit:(.*)"
    return find_items(pattern, text)


def find_notes(text):
    pattern = "Noot:(.*)"
    return find_items(pattern, text)


def find_volgcommissies(text):
    pattern = "Volgcommissie\(s\):(.*)"
    return find_items(pattern, text)


def find_items(pattern, text):
    matches = re.finditer(pattern, text)
    items = []
    matches = list(matches)
    for index, obj in enumerate(matches):
        if index < (len(matches)-1):
            end = matches[index+1].span()[0]
        else:
            end = len(text)
        item ={
            'title': obj.group(1).strip(),
            'start': obj.span()[0],
            'end': end
        }
        items.append(item)
    return items


def pdf_to_text(filepath):
    # based on http://stackoverflow.com/a/26495057/607041
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    # laparams = LAParams()
    laparams = None
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    with open(filepath, 'rb') as filein:
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos=set()
        for page in PDFPage.get_pages(filein, pagenos, maxpages=maxpages, password=password, caching=caching, check_extractable=True):
            interpreter.process_page(page)
        text = retstr.getvalue()
        device.close()
        retstr.close()
    return text


def format_text(text):
    text = format_whitespaces(text)
    text = format_agendapunten(text)
    text = format_dates(text)
    text = add_line_front('Voortouwcommissie:', text)
    text = add_line_front('Document:', text)
    text = add_line_front('Zaak:', text)
    text = add_line_front('Besluit:', text)
    text = add_line_front('Noot:', text)
    text = add_line_front('Volgcommissie\(s\):', text)
    text = add_line_front('Griffier:', text)
    text = add_line_front('Activiteitnummer:', text)
    text = remove_page_numbers(text)
    return text


def format_whitespaces(text):
    pattern = "\s{4,}"
    return re.sub(
        pattern=pattern,
        repl='\n\n',
        string=text
    )


def format_agendapunten(text):
    pattern = "(\d{1,3}\.\s{0,})?Agendapunt:"
    return re.sub(
        pattern=pattern,
        repl=add_double_new_line_front,
        string=text
    )


def format_dates(text):
    pattern = '(\d{1,2}\s\w+\s\d{4})(\w+)'
    return re.sub(
        pattern=pattern,
        repl=add_new_line_after_first_group,
        string=text
    )


def add_new_line_after_first_group(matchobj):
    return str(matchobj.group(1)) + ". " + str(matchobj.group(2))


def remove_page_numbers(text):
    pattern = r'\s+\d{1,2}\s+\n'
    return re.sub(
        pattern=pattern,
        repl='\n\n',
        string=text
    )


def add_line_front(pattern, text):
    return re.sub(
        pattern=pattern,
        repl=add_new_line_front,
        string=text
    )


def add_new_line_front(matchobj):
    return '\n' + str(matchobj.group(0))


def add_double_new_line_front(matchobj):
    return '\n\n' + str(matchobj.group(0))
