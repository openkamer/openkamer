import logging

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


def create_document(overheidnl_document_id, dossier_id=None):
    logger.info('BEGIN')
    document_url = 'https://zoek.officielebekendmakingen.nl/' + str(overheidnl_document_id)
    document_html_url = document_url + '.html'
    logger.info(document_html_url)
    document_id, content_html, title = scraper.documents.get_document_id_and_content(document_html_url)
    metadata = scraper.documents.get_metadata(overheidnl_document_id)
    document_id = overheidnl_document_id

    if metadata['date_published']:
        date_published = metadata['date_published']
    elif metadata['date_submitted']:
        date_published = metadata['date_submitted']
    elif metadata['date_received']:
        date_published = metadata['date_received']
    elif metadata['date_meeting']:
        date_published = metadata['date_meeting']
    else:
        date_published = None

    if 'officiële publicatie' in metadata['title_short']:
        metadata['title_short'] = metadata['title_full']

    if 'submitter' not in metadata:
        metadata['submitter'] = 'undefined'
    if metadata['receiver']:
        metadata['submitter'] = metadata['receiver']

    content_html = update_document_html_links(content_html)

    properties = {
        'dossier': None,
        'title_full': metadata['title_full'],
        'title_short': metadata['title_short'],
        'publication_type': metadata['publication_type'],
        'types': metadata['types'],
        'publisher': metadata['publisher'],
        'date_published': date_published,
        'source_url': document_html_url,
        'content_html': content_html,
    }

    document, created = Document.objects.update_or_create(
        document_id=document_id,
        defaults=properties
    )
    category_list = get_categories(text=metadata['category'], category_class=CategoryDocument, sep_char='|')
    document.categories.add(*category_list)

    submitters = metadata['submitter'].split('|')
    for submitter in submitters:
        create_submitter(document, submitter, date_published)

    related_document_ids = scraper.documents.get_related_document_ids(document_url)
    logger.info('END')
    return document, related_document_ids, metadata


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
        active_persons = get_active_persons(date)
        persons_similar = active_persons.filter(surname__iexact=surname).exclude(initials='').exclude(
            forename='')
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
