import logging
from typing import List

import lxml
import re

from django.db import transaction
from django.urls import resolve, Resolver404
from django.urls import reverse

from tkapi.persoon import Persoon as TKPersoon
from tkapi.document import Document as TKDocument
from tkapi.commissie import Commissie as TKCommissie
from tkapi.document import DocumentActor as TKDocumentActor
from tkapi.zaak import Zaak as TKZaak

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

    def __init__(self, document_id, tk_document: TKDocument, tk_zaak: TKZaak, metadata, content_html):
        self.document_id = document_id
        self.tk_document = tk_document
        self.tk_zaak = tk_zaak
        self._metadata = metadata
        self.content_html = update_document_html_links(content_html)

    @property
    def url(self):
        document_id = re.sub(r'-\(.*\)', '', self.document_id)  # Rijkswet ID is not used in url
        return 'https://zoek.officielebekendmakingen.nl/{}.html'.format(document_id)

    @property
    def date_published(self):
        return self.tk_document.datum

    @property
    def category(self):
        return self._metadata['category']

    @property
    def submitters(self) -> List[TKPersoon]:
        actors = []
        if self.tk_document.actors:
            actors = [actor.persoon for actor in self.tk_document.actors if actor.persoon and actor.persoon.achternaam]
        if not actors:
            actors = [actor.persoon for actor in self.tk_zaak.actors if actor.persoon and actor.persoon.achternaam]
        return actors

    @property
    def submitters_commissie(self) -> List[TKCommissie]:
        actors = []
        if self.tk_document.actors:
            actors = [actor.commissie for actor in self.tk_document.actors if actor.commissie]
        if not actors:
            actors = [actor.commissie for actor in self.tk_zaak.actors if actor.commissie]
        return actors

    @property
    def submitters_names(self) -> List[str]:
        names = []
        if self.tk_document.actors:
            names = [actor.naam for actor in self.tk_document.actors if actor.naam]
        if not names:
            names = [actor.naam for actor in self.tk_zaak.actors if actor.naam]
        return names


class DocumentFactory(object):

    def get_document_data(self, tk_document: TKDocument, overheidnl_document_id):
        logger.info(overheidnl_document_id)
        metadata = scraper.documents.get_metadata(overheidnl_document_id)
        overheidnl_document_id = metadata['overheidnl_document_id'] if metadata['overheidnl_document_id'] else overheidnl_document_id
        content_html = scraper.documents.get_html_content(overheidnl_document_id)
        tk_zaak = tk_document.zaken[0] if tk_document.zaken else None
        return DocumentData(
            overheidnl_document_id,
            tk_document=tk_document,
            tk_zaak=tk_zaak,
            metadata=metadata,
            content_html=content_html
        )

    def create_document(self, tk_document: TKDocument, overheidnl_document_id, dossier_id=None, dossier=None):
        logger.info('BEGIN')
        document_data = self.get_document_data(tk_document, overheidnl_document_id)

        if dossier is None:
            dossier = self.get_or_create_dossier(dossier_id)

        properties = {
            'dossier': dossier,
            'title_full': tk_document.onderwerp,
            'title_short': tk_document.titel,
            'publication_type': document_data.tk_document.soort.value,
            'date_published': document_data.date_published,
            'source_url': document_data.url,
            'content_html': document_data.content_html,
        }

        document = self.create_or_update_document(document_data, properties)
        logger.info('END')
        return document

    def create_kamervraag_document(self, tk_document: TKDocument, overheidnl_document_id):
        logger.info('BEGIN')
        document_data = self.get_document_data(tk_document, overheidnl_document_id)

        properties = {
            'dossier': None,
            'title_full': tk_document.onderwerp,
            'title_short': tk_document.onderwerp,
            'publication_type': tk_document.soort.value,
            'date_published': document_data.date_published,
            'source_url': document_data.url,
            'content_html': document_data.content_html,
        }

        document = self.create_or_update_document(document_data, properties)
        logger.info('END')
        return document, document_data._metadata['vraagnummer']

    @staticmethod
    def create_or_update_document(document_data: DocumentData, properties) -> Document:
        if not document_data.date_published:
            logger.error('No published date for document: ' + str(document_data.document_id))

        document, created = Document.objects.update_or_create(
            document_id=document_data.document_id,
            defaults=properties
        )
        category_list = get_categories(text=document_data.category, category_class=CategoryDocument)
        document.categories.add(*category_list)
        SubmitterFactory.create_submitters(document, document_data)
        return document

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
    def create_submitters(document: Document, document_data: DocumentData):
        Submitter.objects.filter(document=document).delete()
        if document_data.submitters:
            for submitter in document_data.submitters:
                SubmitterFactory.create_submitter(document, document_data.date_published, tk_person=submitter)
        else:
            for name in document_data.submitters_names:
                if 'commissie' in name.lower():
                    # TODO BR: extend submitters to be a commissie instead of person only
                    continue
                SubmitterFactory.create_submitter(document, document_data.date_published, name=name)

    @staticmethod
    @transaction.atomic
    def create_submitter(document: Document, date, tk_person: TKPersoon = None, name=None):
        person = None

        if not tk_person:
            logger.warning('No document submitter found for document: {}'.format(document.document_id))
        else:
            persons = Person.objects.filter(tk_id=tk_person.id)
            if len(persons):
                person = persons[0]

            if person is None:
                logger.warning('No person found for tk_persoon: {} ({})'.format(tk_person.achternaam, tk_person.initialen))

        if person is None:
            if tk_person:
                surname = tk_person.achternaam
                surname_prefix = tk_person.tussenvoegsel
                initials = tk_person.initialen
            else:
                initials, surname, surname_prefix = parse_name_surname_initials(name)
            person = Person.find_surname_initials(surname=surname, initials=initials)

        if not person:
            logger.warning('Cannot find person: {} ({}). Creating new person!'.format(surname, initials))
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
