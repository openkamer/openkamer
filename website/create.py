import logging
import os
import re
import requests
from requests.exceptions import ConnectionError, ConnectTimeout
import traceback
import uuid

from pdfminer.pdfparser import PDFSyntaxError

from django.db import transaction

from wikidata import wikidata

from person.models import Person

from government.models import Government
from government.models import Ministry
from government.models import GovernmentPosition
from government.models import GovernmentMember

from parliament.models import PoliticalParty
from parliament.models import PartyMember
from parliament.models import ParliamentMember
from parliament.util import parse_name_initials_surname
from parliament.util import parse_name_surname_initials

from document.models import Agenda
from document.models import AgendaItem
from document.models import BesluitenLijst
from document.models import BesluitItem
from document.models import BesluitItemCase
from document.models import Document
from document.models import Dossier
from document.models import Kamerstuk
from document.models import Submitter
from document.models import Voting
from document.models import Vote
from document.models import VoteParty
from document.models import VoteIndividual

import scraper.besluitenlijst
import scraper.documents
import scraper.government
import scraper.persons
import scraper.votings

logger = logging.getLogger(__name__)


@transaction.atomic
def create_governments():
    # Rutte I : Q168828
    # Rutte II : Q1638648
    government_ids = ['Q1638648', 'Q168828']
    for wikidata_id in government_ids:
        create_government(wikidata_id)


@transaction.atomic
def create_government(wikidata_id, max_members=None):
    gov_info = scraper.government.get_government(wikidata_id)
    government, created = Government.objects.get_or_create(
        name=gov_info['name'],
        date_formed=gov_info['start_date'],
        date_dissolved=gov_info['end_date'],
        wikidata_id=wikidata_id
    )
    create_government_members(government, max_members=max_members)
    return government


@transaction.atomic
def create_government_members(government, max_members=None):
    members_created = []
    members = scraper.government.get_government_members(government.wikidata_id, max_members=max_members)
    for member in members:
        ministry = create_ministry(government, member)
        position = create_government_position(government, member, ministry)
        person = create_person(member['wikidata_id'], member['name'])
        gov_member = create_goverment_member(government, member, person, position)
        members_created.append(gov_member)
    return members_created


@transaction.atomic
def create_ministry(government, member):
    ministry = None
    if 'ministry' in member:
        ministry, created = Ministry.objects.get_or_create(name=member['ministry'].lower(), government=government)
    return ministry


@transaction.atomic
def create_goverment_member(government, member, person, position):
    start_date = government.date_formed
    if 'start_date' in member:
        start_date = member['start_date']
    end_date = None
    if 'end_date' in member:
        end_date = member['end_date']
    member = GovernmentMember.objects.get_or_create(
        person=person,
        position=position,
        start_date=start_date,
        end_date=end_date
    )
    return member


@transaction.atomic
def create_person(wikidata_id, fullname):
    persons = Person.objects.filter(wikidata_id=wikidata_id)
    if persons.exists():
        person = persons[0]
    else:
        forename = wikidata.get_given_name(wikidata_id)
        if not forename:
            forename = fullname.split(' ')[0]
        surname = fullname.replace(forename, '').strip()
        prefix = Person.find_prefix(surname)
        if prefix:
            surname = surname.replace(prefix + ' ', '')
        person = Person.objects.create(
            forename=forename,
            surname=surname,
            surname_prefix=prefix,
            wikidata_id=wikidata_id
        )
        person.update_info()
        person.save()
        if person.parlement_and_politiek_id:
            person.initials = scraper.persons.get_initials(person.parlement_and_politiek_id)
            person.save()
        assert person.wikidata_id == wikidata_id
    party_members = PartyMember.objects.filter(person=person)
    if not party_members.exists():
        memberships = wikidata.get_political_party_memberships(wikidata_id)
        for membership in memberships:
            parties = PoliticalParty.objects.filter(wikidata_id=membership['wikidata_id'])
            if parties.exists():
                party = parties[0]
            else:
                logger.error('political party with wikidata id: ' + str(membership['wikidata_id']) + ' does not exist')
                continue
            PartyMember.objects.create(
                person=person,
                party=party,
                joined=membership['start_date'],
                left=membership['end_date']
            )
    return person


@transaction.atomic
def create_government_position(government, member, ministry):
    position_type = GovernmentPosition.find_position_type(member['position'])
    positions = GovernmentPosition.objects.filter(
        ministry=ministry,
        position=position_type,
        government=government,
        extra_info=member['position_name'],
    )
    if positions.exists():
        if positions.count() > 1:
            logger.error('more than one GovernmentPosition found for ministry: ' + str(ministry) + ' and position: ' + str(position_type))
        position = positions[0]
    else:
        position = GovernmentPosition.objects.create(
            ministry=ministry,
            position=position_type,
            government=government,
            extra_info=member['position_name'],
        )
    return position


def create_dossier_retry_on_error(dossier_id, max_tries=3):
    dossier_id = str(dossier_id)
    tries = 0
    while True:
        try:
            tries += 1
            create_or_update_dossier(dossier_id)
        except (ConnectionError, ConnectTimeout) as e:
            logger.error(traceback.format_exc())
            if tries < max_tries:
                logger.error('trying again!')
                continue
            logger.error('max tries reached, skipping dossier: ' + dossier_id)
        break


@transaction.atomic
def create_or_update_dossier(dossier_id):
    logger.info('BEGIN - dossier id: ' + str(dossier_id))
    Dossier.objects.filter(dossier_id=dossier_id).delete()
    dossier = Dossier.objects.create(dossier_id=dossier_id)
    search_results = scraper.documents.search_politieknl_dossier(dossier_id)
    for result in search_results:
        # skip eerste kamer documents, first focus on the tweede kamer
        # TODO: handle eerste kamer documents
        if 'eerste kamer' in result['publisher'].lower():
            logger.info('skipping Eerste Kamer document')
            continue
        # skip documents of some types and/or sources, no models implemented yet
        # TODO: handle all document types
        if 'Staatscourant' in result['type']:
            logger.info('Staatscourant, skip for now')
            continue

        document_id, content_html = scraper.documents.get_document_id_and_content(result['page_url'])
        if not document_id:
            logger.warning('No document id found, will not create document')
            continue

        metadata = scraper.documents.get_metadata(document_id)

        if metadata['date_published']:
            date_published = metadata['date_published']
        else:
            date_published = result['date_published']

        if 'submitter' not in metadata:
            metadata['submitter'] = 'undefined'

        document = Document.objects.create(
            dossier=dossier,
            document_id=document_id,
            title_full=metadata['title_full'],
            title_short=metadata['title_short'],
            publication_type=metadata['publication_type'],
            category=metadata['category'],
            publisher=metadata['publisher'],
            date_published=date_published,
            content_html=content_html,
        )

        submitters = metadata['submitter'].split('|')
        for submitter in submitters:
            create_submitter(document, submitter)

        if metadata['is_kamerstuk']:
            create_kamerstuk(document, dossier_id, metadata, result)

        if metadata['is_agenda']:
            create_agenda(document, metadata)

    create_votings(dossier_id)
    logger.info('END - dossier id: ' + str(dossier_id))
    return dossier


@transaction.atomic
def create_kamerstuk(document, dossier_id, metadata, result):
    logger.info('BEGIN')
    logger.info('document: ' + str(document))
    title_parts = metadata['title_full'].split(';')
    type_short = ''
    type_long = ''
    if len(title_parts) > 2:
        type_short = title_parts[1].strip()
        type_long = title_parts[2].strip()
    if "Bijlage" in result['type']:
        type_short = 'Bijlage'
        type_long = 'Bijlage'
    if type_short == '':
        type_short = document.title_short
    if type_long == '':
        type_long = document.title_full
    original_id = find_original_kamerstuk_id(dossier_id, type_long)
    stuk = Kamerstuk.objects.create(
        document=document,
        id_main=dossier_id,
        id_sub=metadata['id_sub'].zfill(2),
        type_short=type_short,
        type_long=type_long,
        original_id=original_id
    )
    logger.info('kamerstuk created: ' + str(stuk))
    logger.info('END')


def find_original_kamerstuk_id(dossier_id, type_long):
    if 'gewijzigd' not in type_long.lower():
        return ''
    result_dossier = re.search(r"t.v.v.\s*(?P<main_id>[0-9]*)", type_long)
    result_document = re.search(r"nr.\s*(?P<sub_id>[0-9]*)", type_long)
    main_id = ''
    sub_id = ''
    if result_dossier and 'main_id' in result_dossier.groupdict():
        main_id = result_dossier.group('main_id')
    if result_document and 'sub_id' in result_document.groupdict():
        sub_id = result_document.group('sub_id')
    if main_id and sub_id:
        return main_id + '-' + sub_id
    elif sub_id:
        return str(dossier_id) + '-' + sub_id
    elif 'voorstel van wet' in type_long.lower():
        return str(dossier_id) + '-voorstel_van_wet'
    return ''


@transaction.atomic
def create_submitter(document, submitter):
    has_initials = len(submitter.split('.')) > 1
    initials = ''
    surname = submitter
    if has_initials:
        initials, surname = parse_name_initials_surname(submitter)
    person = Person.find(surname=surname, initials=initials)
    if not person:
        logger.warning('Cannot find person: ' + str(surname) + ' ' + str(initials) + '. Creating new person!')
        person = Person.objects.create(surname=surname, initials=initials)
    Submitter.objects.create(person=person, document=document)


@transaction.atomic
def create_agenda(document, metadata):
    logger.info('create agenda')
    agenda = Agenda.objects.create(
        agenda_id=document.document_id,
        document=document,
    )
    agenda_items = []
    for n in metadata['behandelde_dossiers']:
        dossiers = Dossier.objects.filter(dossier_id=n)
        if dossiers:
            dossier = dossiers[0]
            agenda_item = AgendaItem(
                agenda=agenda,
                dossier=dossier,
                item_text=n,
            )
        else:
            agenda_item = AgendaItem(
                agenda=agenda,
                item_text=n,
            )
        agenda_items.append(agenda_item)
    AgendaItem.objects.bulk_create(agenda_items)
    return agenda


def create_or_update_agenda(agenda_id):
    #TODO: implement
    agendas = Agenda.objects.filter(agenda_id=agenda_id)
    if agendas:
        #        pass
        agenda = agendas[0]
        agenda.document.delete()
        agenda.delete()
    else:
        pass

    return


@transaction.atomic
def create_votings(dossier_id):
    logger.info('dossier id: ' + str(dossier_id))
    voting_results = scraper.votings.get_votings_for_dossier(dossier_id)
    logger.info('votings found: ' + str(len(voting_results)))
    for voting_result in voting_results:
        result = get_result_choice(voting_result.get_result())
        if result is None:
            logger.error('Could not interpret vote result: ' + voting_result.get_result())
            assert False
        document_id = voting_result.get_document_id()
        if not document_id:
            logger.error('Voting has no document id. This is probably a modification of an existing document and does not (yet?) have a document id.')
            id_main = dossier_id
        else:
            id_main = document_id.split('-')[0]
        dossiers = Dossier.objects.filter(dossier_id=id_main)
        assert dossiers.count() == 1
        voting_obj = Voting(dossier=dossiers[0], date=voting_result.date, result=result, is_dossier_voting=voting_result.is_dossier_voting())
        if document_id and len(document_id.split('-')) == 2:
            id_sub = document_id.split('-')[1]
            kamerstukken = Kamerstuk.objects.filter(id_main=id_main, id_sub=id_sub)
            if kamerstukken.exists():
                voting_obj.kamerstuk = kamerstukken[0]
            else:
                logger.warning('Kamerstuk ' + voting_result.get_document_id() + ' not found in database. Kamerstuk is probably not yet published.')
        voting_obj.save()
        if voting_result.is_individual():
            create_votes_individual(voting_obj, voting_result.votes)
        else:
            create_votes_party(voting_obj, voting_result.votes)


@transaction.atomic
def create_votes_party(voting, votes):
    for vote in votes:
        party = PoliticalParty.find_party(vote.party_name)
        assert party
        VoteParty.objects.create(voting=voting, party=party, number_of_seats=vote.number_of_seats,
                                 decision=get_decision(vote.decision), details=vote.details)


@transaction.atomic
def create_votes_individual(voting, votes):
    for vote in votes:
        initials, surname = parse_name_surname_initials(vote.parliament_member)
        parliament_member = ParliamentMember.find(surname=surname, initials=initials)
        if not parliament_member:
            logger.error('parliament member not found for vote: ' + str(vote))
            logger.error('creating vote with empty parliament member')
            if voting.kamerstuk:
                logger.error('on kamerstuk: ' + str(voting.kamerstuk) + ', in dossier: ' + str(voting.kamerstuk.document.dossier) + ', for name: ' + surname + ' ' + initials)
            else:
                logger.error('voting.kamerstuk does not exist')
        VoteIndividual.objects.create(voting=voting, parliament_member=parliament_member, number_of_seats=vote.number_of_seats,
                                      decision=get_decision(vote.decision), details=vote.details)


def get_result_choice(result_string):
    if 'aangenomen' in result_string.lower():
        return Voting.AANGENOMEN
    elif 'verworpen' in result_string.lower():
        return Voting.VERWORPEN
    elif 'ingetrokken' in result_string.lower():
        return Voting.INGETROKKEN
    elif 'aangehouden' in result_string.lower():
        return Voting.AANGEHOUDEN
    return None


def get_decision(decision_string):
    decision_string = decision_string.lower()
    if 'for' in decision_string:
        return Vote.FOR
    elif 'against' in decision_string:
        return Vote.AGAINST
    elif 'none' in decision_string:
        return Vote.NONE
    elif 'mistake' in decision_string:
        return Vote.MISTAKE
    return None


def create_besluitenlijsten(max_results_per_commission=None):
    commissies = scraper.besluitenlijst.get_voortouwcommissies_besluiten_urls()
    for commissie in commissies:
        urls = scraper.besluitenlijst.get_besluitenlijsten_urls(commissie['url'], max_results=max_results_per_commission)
        for url in urls:
            try:
                create_besluitenlijst(url)
            except PDFSyntaxError as e:
                logger.error('failed to download and parse besluitenlijst with url: ' + url)
            except TypeError as e:
                # pdfminer error that may cause this has been reported here: https://github.com/euske/pdfminer/pull/89
                logger.error(traceback.format_exc())
                logger.error('error while converting besluitenlijst pdf to text')


@transaction.atomic
def create_besluitenlijst(url):
    logger.info('BEGIN')
    logger.info('url: ' + url)
    filename = uuid.uuid4().hex + '.pdf'
    filepath = 'data/tmp/' + filename
    with open(filepath, 'wb') as pdffile:
        response = requests.get(url)
        response.raise_for_status()
        pdffile.write(response.content)
    text = scraper.besluitenlijst.besluitenlijst_pdf_to_text(filepath)
    os.remove(filepath)
    bl = scraper.besluitenlijst.create_besluitenlijst(text)
    BesluitenLijst.objects.filter(activity_id=bl.activiteitnummer).delete()
    BesluitenLijst.objects.filter(url=url).delete()
    besluiten_lijst = BesluitenLijst.objects.create(
        title=bl.title,
        commission=bl.voortouwcommissie,
        activity_id=bl.activiteitnummer,
        date_published=bl.date_published,
        url=url
    )

    for item in bl.items:
        besluit_item = BesluitItem.objects.create(
            title=item.title,
            besluiten_lijst=besluiten_lijst
        )
        for case in item.cases:
            BesluitItemCase.objects.create(
                title=case.title,
                besluit_item = besluit_item,
                decisions=case.create_str_list(case.decisions, BesluitItemCase.SEP_CHAR),
                notes=case.create_str_list(case.notes, BesluitItemCase.SEP_CHAR),
                related_commissions=case.create_str_list(case.volgcommissies, BesluitItemCase.SEP_CHAR),
                related_document_ids=case.create_str_list(case.related_document_ids, BesluitItemCase.SEP_CHAR),
            )
    logger.info('END')
    return besluiten_lijst
