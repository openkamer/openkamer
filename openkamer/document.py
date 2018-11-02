import logging
from enum import Enum

import lxml
import re

from django.db import transaction
from django.urls import resolve, Resolver404
from django.urls import reverse

import scraper.documents

from person.util import parse_name_surname_initials
from person.util import parse_surname_comma_surname_prefix
from person.models import Person

from government.models import GovernmentMember
from parliament.models import ParliamentMember
from parliament.models import PartyMember

from document.models import CategoryDocument
from document.models import Document
from document.models import Dossier
from document.models import Kamerstuk
from document.models import Submitter


logger = logging.getLogger(__name__)


class DocumentData(object):

    def __init__(self, document_id, metadata, content_html, title, document_url):
        self.document_id = document_id
        self.metadata = metadata
        self.content_html = update_document_html_links(content_html)
        self.title = title
        self.document_url = document_url
        self.document_html_url = document_url + '.html'
        self.update_metatdata()

    @property
    def date_published(self):
        if self.metadata['date_published']:
            return self.metadata['date_published']
        elif self.metadata['date_submitted']:
            return self.metadata['date_submitted']
        elif self.metadata['date_received']:
            return self.metadata['date_received']
        return None

    def update_metatdata(self):
        if 'officiële publicatie' in self.metadata['title_short']:
            self.metadata['title_short'] = self.metadata['title_full']
        if 'submitter' not in self.metadata:
            self.metadata['submitter'] = 'undefined'
        if self.metadata['receiver']:
            self.metadata['submitter'] = self.metadata['receiver']


class DocumentFactory(object):

    class DocumentType(Enum):
        KAMERSTUK = 'Kamerstuk'
        KAMERVRAAG = 'Kamervraag'

    def __init__(self, document_type=None):
        logger.info('DocumentFactory()')
        self.scraper = None
        if document_type == self.DocumentType.KAMERVRAAG:
            self.scraper = scraper.documents.get_kamervraag_document_id_and_content
        elif document_type == self.DocumentType.KAMERSTUK:
            self.scraper = scraper.documents.get_document_id_and_content
        elif document_type is None:
            self.scraper = scraper.documents.get_document_id_and_content

    def get_document(self, overheidnl_document_id):
        document_url = 'https://zoek.officielebekendmakingen.nl/' + str(overheidnl_document_id)
        document_html_url = document_url + '.html'
        document_id, content_html, title = self.scraper(document_html_url)
        metadata = scraper.documents.get_metadata(overheidnl_document_id)
        document_id = overheidnl_document_id
        return DocumentData(document_id, metadata, content_html, title, document_url)

    def create_document(self, overheidnl_document_id, dossier_id=None, dossier=None):
        logger.info('BEGIN')
        document_data = self.get_document(overheidnl_document_id)
        metadata = document_data.metadata

        if dossier is None:
            dossier = self.get_or_create_dossier(dossier_id)

        properties = {
            'dossier': dossier,
            'title_full': metadata['title_full'],
            'title_short': metadata['title_short'],
            'publication_type': metadata['publication_type'],
            'types': metadata['types'],
            'publisher': metadata['publisher'],
            'date_published': document_data.date_published,
            'source_url': document_data.document_html_url,
            'content_html': document_data.content_html,
        }

        document, related_document_ids = self.create_document_and_related(document_data, properties)
        logger.info('END')
        return document, related_document_ids, metadata

    def create_kamervraag_document(self, overheidnl_document_id):
        logger.info('BEGIN')
        document_data = self.get_document(overheidnl_document_id)
        metadata = document_data.metadata

        properties = {
            'dossier': None,
            'title_full': document_data.title,
            'title_short': metadata['title_full'],
            'publication_type': metadata['publication_type'],
            'types': metadata['types'],
            'publisher': metadata['publisher'],
            'date_published': document_data.date_published,
            'source_url': document_data.document_html_url,
            'content_html': document_data.content_html,
        }

        document, related_document_ids = self.create_document_and_related(document_data, properties)
        logger.info('END')
        return document, related_document_ids, metadata['vraagnummer']

    @staticmethod
    def create_document_and_related(document_data, properties):
        document, created = Document.objects.update_or_create(
            document_id=document_data.document_id,
            defaults=properties
        )
        category_list = get_categories(text=document_data.metadata['category'], category_class=CategoryDocument)
        document.categories.add(*category_list)

        submitters = document_data.metadata['submitter'].split('|')
        for submitter in submitters:
            SubmitterFactory.create_submitter(document, submitter, document_data.date_published)

        related_document_ids = scraper.documents.get_related_document_ids(document_data.document_url)
        return document, related_document_ids

    @staticmethod
    def get_or_create_dossier(dossier_id):
        dossiers = Dossier.objects.filter(dossier_id=dossier_id)
        dossier = None
        if dossiers.exists():
            dossier = dossiers[0]
        return dossier


def update_document_html_links(content_html):
    if not content_html:
        return content_html
    tree = lxml.html.fromstring(content_html)
    a_elements = tree.xpath('//a')
    for element in a_elements:
        if not 'href' in element.attrib:
            continue
        url = element.attrib['href']
        new_url = create_new_url(url)
        element.attrib['href'] = new_url
    return lxml.html.tostring(tree).decode('utf-8')


def create_new_url(url):
    match_kamerstuk = re.match("kst-(\d+)-(\d+)", url)
    match_dossier = re.match("/dossier/(\d+)", url)
    new_url = ''
    if match_kamerstuk:
        dossier_id = match_kamerstuk.group(1)
        sub_id = match_kamerstuk.group(2)
        kamerstukken = Kamerstuk.objects.filter(id_main=dossier_id, id_sub=sub_id)
        if kamerstukken.exists():
            new_url = reverse('kamerstuk', args=(dossier_id, sub_id,))
    elif match_dossier:
        dossier_id = match_dossier.group(1)
        if Dossier.objects.filter(dossier_id=dossier_id).exists():
            new_url = reverse('dossier-timeline', args=(dossier_id,))
    if not new_url:
        try:
            resolve(url)
            openkamer_url = True
        except Resolver404:
            openkamer_url = False
        if openkamer_url or url[0] == '#' or 'http' in url:  # openkamer, anchor or external url
            new_url = url
        else:
            if url[0] != '/':
                url = '/' + url
            new_url = 'https://zoek.officielebekendmakingen.nl' + url
    return new_url


class SubmitterFactory(object):

    @staticmethod
    @transaction.atomic
    def create_submitter(document, submitter, date):
        # TODO: fix this ugly if else mess
        has_initials = len(submitter.split('.')) > 1
        initials = ''
        if has_initials:
            initials, surname, surname_prefix = parse_name_surname_initials(submitter)
        else:
            surname, surname_prefix = parse_surname_comma_surname_prefix(submitter)
        if initials == 'C.S.':  # this is an abbreviation used in old metadata to indicate 'and usual others'
            initials = ''

        person = Person.find_surname_initials(surname=surname, initials=initials)
        if surname == 'JAN JACOB VAN DIJK':  # 'Jan Jacob van Dijk' and ' Jasper van Dijk' have the same surname and initials, to solve this they have included the forename in the surname
            person = Person.objects.filter(forename='Jan Jacob', surname_prefix='van', surname='Dijk', initials='J.J.')[0]
        if surname == 'JASPER VAN DIJK':
            person = Person.objects.filter(forename='Jasper', surname_prefix='van', surname='Dijk', initials='J.J.')[0]
        if surname == 'JAN DE VRIES':
            person = Person.objects.filter(forename='Jan', surname_prefix='de', surname='Vries', initials='J.M.')[0]

        if not person:
            active_persons = SubmitterFactory.get_active_persons(date)
            persons_similar = active_persons.filter(surname__iexact=surname).exclude(initials='').exclude(forename='')
            if persons_similar.count() == 1:
                person = persons_similar[0]
        if not person:
            if surname == '' and initials == '':
                persons = Person.objects.filter(surname='', initials='', forename='')
                if persons:
                    person = persons[0]
        if not person:
            persons = Person.objects.filter(surname__iexact=surname, initials__iexact=initials)
            if persons:
                person = persons[0]
        if not person:
            logger.warning('Cannot find person: ' + str(surname) + ' ' + str(initials) + '. Creating new person!')
            person = Person.objects.create(surname=surname, surname_prefix=surname_prefix, initials=initials)

        party_members = PartyMember.get_at_date(person, date)
        party_slug = ''
        if party_members:
            party_slug = party_members[0].party.slug

        submitter, created = Submitter.objects.get_or_create(person=person, document=document, party_slug=party_slug)
        return submitter

    @staticmethod
    def get_active_persons(date):
        pms = ParliamentMember.active_at_date(date)
        gms = GovernmentMember.active_at_date(date)
        person_ids = []
        for pm in pms:
            person_ids.append(pm.person.id)
        for gm in gms:
            person_ids.append(gm.person.id)
        return Person.objects.filter(id__in=person_ids)


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
