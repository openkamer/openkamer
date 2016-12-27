import logging
import os
import re
import time
import traceback
import uuid
from json.decoder import JSONDecodeError

import lxml
import requests
from django.db import transaction
from django.urls import resolve, Resolver404
from django.urls import reverse
from pdfminer.pdfparser import PDFSyntaxError
from requests.exceptions import ConnectionError, ConnectTimeout, ChunkedEncodingError

import scraper.besluitenlijst
import scraper.documents
import scraper.dossiers
import scraper.government
import scraper.parliament_members
import scraper.persons
import scraper.political_parties
import scraper.votings
from document.models import Agenda
from document.models import AgendaItem
from document.models import BesluitItem
from document.models import BesluitItemCase
from document.models import BesluitenLijst
from document.models import CategoryDocument
from document.models import CategoryDossier
from document.models import Document
from document.models import Dossier
from document.models import Kamerstuk
from document.models import Submitter
from document.models import Vote
from document.models import VoteIndividual
from document.models import VoteParty
from document.models import Voting
from government.models import Government
from government.models import GovernmentMember
from government.models import GovernmentPosition
from government.models import Ministry
from parliament.models import Parliament
from parliament.models import ParliamentMember
from parliament.models import PartyMember
from parliament.models import PoliticalParty
from person.models import Person
from person.util import parse_name_surname_initials
from wikidata import wikidata

from website import settings

logger = logging.getLogger(__name__)


@transaction.atomic
def create_parliament_and_government():
    create_parties()
    create_governments()
    create_parliament_members()
    create_party_members()
    for party in PoliticalParty.objects.all():
        party.set_current_parliament_seats()


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
    Government.objects.filter(wikidata_id=wikidata_id).delete()
    government = Government.objects.create(
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
        person = create_person(member['wikidata_id'], member['name'], add_initials=True)
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
    end_date = government.date_dissolved
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
def create_parties():
    parties = scraper.political_parties.search_parties()
    for party_info in parties:
        create_party(party_info['name'], party_info['name_short'])
    set_party_votes_derived_info()


@transaction.atomic
def create_party(name, name_short):
    party = PoliticalParty.find_party(name)
    if party:
        party.delete()
    party = PoliticalParty.objects.create(name=name, name_short=name_short)
    party.update_info(language='nl')
    return party


@transaction.atomic
def create_party_members():
    logger.info('BEGIN')
    persons = Person.objects.filter(wikidata_id__isnull=False)
    for person in persons:
        create_party_members_for_person(person)
    logger.info('END')


@transaction.atomic
def create_party_members_for_person(person):
    logger.info('BEGIN, person: ' + str(person))
    if not person.wikidata_id:
        logger.warning('could not update party member for person: ' + str(person) + ' because person has no wikidata id.')
        return
    PartyMember.objects.filter(person=person).delete()
    wikidata_item = wikidata.WikidataItem(person.wikidata_id)
    memberships = wikidata_item.get_political_party_memberships()
    for membership in memberships:
        parties = PoliticalParty.objects.filter(wikidata_id=membership['wikidata_id'])
        if parties.exists():
            party = parties[0]
        else:
            logger.error('could not find party with wikidata id: ' + str(membership['wikidata_id']))
            continue
        new_member = PartyMember.objects.create(
            person=person,
            party=party,
            joined=membership['start_date'],
            left=membership['end_date']
        )
        logger.info(new_member.joined)
    logger.info('END')


@transaction.atomic
def create_parliament_members_from_tweedekamer_data():
    parliament = Parliament.get_or_create_tweede_kamer()
    members = scraper.parliament_members.search_members()
    for member in members:
        forename = member['forename']
        surname = member['surname']
        if Person.person_exists(forename, surname):
            person = Person.objects.get(forename=forename, surname=surname)
        else:
            person = Person.objects.create(
                forename=forename,
                surname=surname,
                surname_prefix=member['prefix'],
                initials=member['initials']
            )
        party = PoliticalParty.find_party(member['party'])
        party_member = PartyMember.objects.create(person=person, party=party)
        parliament_member = ParliamentMember.objects.create(person=person, parliament=parliament)
        logger.info("new person: " + str(person))
        logger.info("new party member: " + str(party_member))
        logger.info("new parliament member: " + str(parliament_member))


@transaction.atomic
def create_parliament_members(max_results=None, all_members=False):
    logger.info('BEGIN')
    ParliamentMember.objects.all().delete()
    parliament = Parliament.get_or_create_tweede_kamer()
    if all_members:
        member_wikidata_ids = wikidata.search_parliament_member_ids()
    else:
        member_wikidata_ids = wikidata.search_parliament_member_ids_with_start_date()
    counter = 0
    members = []
    for wikidata_id in member_wikidata_ids:
        logger.info('=========================')
        try:
            wikidata_item = wikidata.WikidataItem(wikidata_id)
            person = create_person(wikidata_id, wikidata_item=wikidata_item, add_initials=True)
            logger.info(person)
            logger.info(person.wikipedia_url)
            positions = wikidata_item.get_parliament_positions_held()
            for position in positions:
                parliament_member = ParliamentMember.objects.create(
                    person=person,
                    parliament=parliament,
                    joined=position['start_time'],
                    left=position['end_time']
                )
                logger.info(parliament_member)
                members.append(parliament_member)
        except (JSONDecodeError, ConnectionError, ConnectTimeout, ChunkedEncodingError) as error:
            logger.error(traceback.format_exc())
            logger.error(error)
            logger.error('')
        except:
            logger.error(traceback.format_exc())
            raise
        counter += 1
        if max_results and counter >= max_results:
            logger.info('END: max results reached')
            break
    set_individual_votes_derived_info()
    logger.info('END')
    return members


@transaction.atomic
def set_individual_votes_derived_info():
    """ sets the derived foreign keys in individual votes, needed after parliament members have changed """
    logger.info('BEGIN')
    votes = VoteIndividual.objects.all()
    for vote in votes:
        vote.set_derived()
    logger.info('END')


@transaction.atomic
def set_party_votes_derived_info():
    """ sets the derived foreign keys in party votes, needed after parties have changed """
    logger.info('BEGIN')
    votes = VoteParty.objects.all()
    for vote in votes:
        vote.set_derived()
    logger.info('END')


@transaction.atomic
def create_person(wikidata_id, fullname='', wikidata_item=None, add_initials=False):
    persons = Person.objects.filter(wikidata_id=wikidata_id)
    if not wikidata_item:
        wikidata_item = wikidata.WikidataItem(wikidata_id)
    if persons.exists():
        person = persons[0]
    else:
        if not fullname:
            fullname = wikidata_item.get_label(language='nl')
        forename, surname, surname_prefix = Person.get_name_parts(fullname, wikidata_item)
        person = Person.objects.create(
            forename=forename,
            surname=surname,
            surname_prefix=surname_prefix,
            wikidata_id=wikidata_id
        )
        person.update_info(language='nl', wikidata_item=wikidata_item)
        person.save()
        if add_initials and person.parlement_and_politiek_id:
            person.initials = scraper.persons.get_initials(person.parlement_and_politiek_id)
            person.save()
        assert person.wikidata_id == wikidata_id
    party_members = PartyMember.objects.filter(person=person)
    if not party_members.exists():
        create_party_members_for_person(person)
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
            time.sleep(5)  # wait 5 seconds for external servers to relax
            if tries < max_tries:
                logger.error('trying again!')
                continue
            logger.error('max tries reached, skipping dossier: ' + dossier_id)
        break


@transaction.atomic
def create_or_update_dossier(dossier_id):
    logger.info('BEGIN - dossier id: ' + str(dossier_id))
    Dossier.objects.filter(dossier_id=dossier_id).delete()
    dossier_url = scraper.dossiers.search_dossier_url(dossier_id)
    decision = scraper.dossiers.get_dossier_decision(dossier_url)
    dossier_new = Dossier.objects.create(
        dossier_id=dossier_id,
        is_active=Dossier.is_active_id(dossier_id),
        url=dossier_url,
        decision=decision
    )
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

        document_id, content_html, title = scraper.documents.get_document_id_and_content(result['page_url'])
        if not document_id:
            logger.error('No document id found for url: ' + result['page_url'] + ' - will not create document')
            continue

        metadata = scraper.documents.get_metadata(document_id)

        if metadata['date_published']:
            date_published = metadata['date_published']
        else:
            date_published = result['date_published']

        if 'submitter' not in metadata:
            metadata['submitter'] = 'undefined'

        if 'dossier_id' in metadata:
            main_dossier_id = metadata['dossier_id'].split(';')[0].strip()
            main_dossier_id = main_dossier_id.split('-')[0]  # remove rijkswetdossier id, for example 34158-(R2048)
            if main_dossier_id != '' and str(main_dossier_id) != str(dossier_id):
                dossier_for_document, created = Dossier.objects.get_or_create(dossier_id=main_dossier_id)
            else:
                dossier_for_document = dossier_new

        documents = Document.objects.filter(document_id=document_id)
        if documents.exists():
            logger.warning('document with id: ' + document_id + ' already exists, skip creating document.')
            continue

        content_html = update_document_html_links(content_html)

        document = Document.objects.create(
            dossier=dossier_for_document,
            document_id=document_id,
            title_full=metadata['title_full'],
            title_short=metadata['title_short'],
            publication_type=metadata['publication_type'],
            publisher=metadata['publisher'],
            date_published=date_published,
            content_html=content_html,
        )
        category_list = get_categories(text=metadata['category'], category_class=CategoryDocument, sep_char='|')
        document.categories.add(*category_list)

        submitters = metadata['submitter'].split('|')
        for submitter in submitters:
            create_submitter(document, submitter)

        if metadata['is_kamerstuk']:
            is_attachement = "Bijlage" in result['type']
            create_kamerstuk(document, dossier_for_document.dossier_id, title, metadata, is_attachement)
            category_list = get_categories(text=metadata['category'], category_class=CategoryDossier, sep_char='|')
            dossier_for_document.categories.add(*category_list)

        if metadata['is_agenda']:
            create_agenda(document, metadata)

    create_votings(dossier_id)
    dossier_new.set_derived_fields()
    logger.info('END - dossier id: ' + str(dossier_id))
    return dossier_new


def create_wetsvoorstellen_active(skip_existing=False, max_tries=3):
    logger.info('BEGIN')
    dossier_ids = Dossier.get_active_dossier_ids()
    failed_dossiers = create_wetsvoorstellen(dossier_ids, skip_existing=skip_existing, max_tries=max_tries)
    logger.info('END')
    return failed_dossiers


def create_wetsvoorstellen_inactive(skip_existing=False, max_tries=3):
    logger.info('BEGIN')
    dossier_ids = Dossier.get_inactive_dossier_ids()
    failed_dossiers = create_wetsvoorstellen(dossier_ids, skip_existing=skip_existing, max_tries=max_tries)
    logger.info('END')
    return failed_dossiers


def create_wetsvoorstellen_all(skip_existing=False, max_tries=3):
    logger.info('BEGIN')
    failed_dossiers = create_wetsvoorstellen_active(skip_existing=skip_existing, max_tries=max_tries)
    failed_dossiers += create_wetsvoorstellen_inactive(skip_existing=skip_existing, max_tries=max_tries)
    logger.info('END')
    return failed_dossiers


def create_wetsvoorstellen(dossier_ids, skip_existing=False, max_tries=3):
    logger.info('BEGIN')
    failed_dossiers = []
    for dossier_id in dossier_ids:
        dossiers = Dossier.objects.filter(dossier_id=dossier_id)
        if skip_existing and dossiers.exists():
            logger.info('dossier already exists, skip')
            continue
        try:
            create_dossier_retry_on_error(dossier_id=dossier_id, max_tries=max_tries)
        except Exception as e:
            failed_dossiers.append(dossier_id)
            logger.error('error for dossier id: ' + str(dossier_id))
            logger.error(traceback.format_exc())
    logger.info('END')
    return failed_dossiers


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


@transaction.atomic
def create_kamerstuk(document, dossier_id, title, metadata, is_attachement):
    logger.info('BEGIN')
    logger.info('document: ' + str(document))
    title_parts = metadata['title_full'].split(';')
    type_short = ''
    type_long = ''
    if len(title_parts) > 2:
        type_short = title_parts[1].strip()
        type_long = title_parts[2].strip()
    if is_attachement:
        type_short = 'Bijlage'
        type_long = 'Bijlage'
    if type_short == '':
        type_short = document.title_short
    if type_short == 'officiële publicatie':
        type_short = title
    if type_long == '':
        type_long = document.title_full
    original_id = find_original_kamerstuk_id(dossier_id, type_long)
    stuk = Kamerstuk.objects.create(
        document=document,
        id_main=dossier_id,
        id_sub=metadata['id_sub'],
        type_short=type_short,
        type_long=type_long,
        original_id=original_id
    )
    logger.info('kamerstuk created: ' + str(stuk))
    logger.info('END')


def find_original_kamerstuk_id(dossier_id, type_long):
    if 'gewijzigd' not in type_long.lower() and 'nota van wijziging' not in type_long.lower():
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
    elif 'voorstel van wet' in type_long.lower() or 'nota van wijziging' in type_long.lower():
        return str(dossier_id) + '-voorstel_van_wet'
    return ''


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
    return lxml.html.tostring(tree)


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
def create_submitter(document, submitter):
    has_initials = len(submitter.split('.')) > 1
    initials = ''
    surname = submitter
    if has_initials:
        initials, surname, surname_prefix = parse_name_surname_initials(submitter)
    if initials == 'C.S.':  # this is an abbreviation used in old metadata to indicate 'and usual others'
        initials = ''
    person = Person.find_surname_initials(surname=surname, initials=initials)
    if not person:
        logger.warning('Cannot find person: ' + str(surname) + ' ' + str(initials) + '. Creating new person!')
        person = Person.objects.create(surname=surname, initials=initials)
    return Submitter.objects.create(person=person, document=document)


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
    logger.info('BEGIN')
    logger.info('dossier id: ' + str(dossier_id))
    voting_results = scraper.votings.get_votings_for_dossier(dossier_id)
    logger.info('votings found: ' + str(len(voting_results)))
    for voting_result in voting_results:
        if not voting_result.get_result():
            logger.warning('no result found for voting, probaly not voted yet, voting date: ' + str(voting_result.date))
            continue
        document_id = voting_result.get_document_id_without_rijkswet()
        if not document_id:
            logger.error('Voting has no document id. This is probably a modification of an existing document and does not (yet?) have a document id.')
            continue
        id_main = document_id.split('-')[0]
        dossiers = Dossier.objects.filter(dossier_id=id_main)
        if dossiers.count() != 1:
            logger.error('number of dossiers found: ' + str(dossiers.count()) + ', which is not 1, so we have to skip this voting')
            continue
        assert dossiers.count() == 1
        result = get_result_choice(voting_result.get_result())
        voting_obj = Voting(dossier=dossiers[0], date=voting_result.date, result=result, is_dossier_voting=voting_result.is_dossier_voting())
        if document_id and len(document_id.split('-')) == 2:
            id_sub = document_id.split('-')[1]
            kamerstukken = Kamerstuk.objects.filter(id_main=id_main, id_sub=id_sub)
            if kamerstukken.exists():
                kamerstuk = kamerstukken[0]
                voting_obj.kamerstuk = kamerstuk
                if kamerstuk.voting and kamerstuk.voting.date > voting_obj.date:  # A voting can be postponed and later voted on, we do not save the postponed voting if there is a newer voting
                    logger.info('newer voting for this kamerstuk already exits, skip this voting')
                    continue
                elif kamerstuk.voting:
                    kamerstuk.voting.delete()
            else:
                logger.error('Kamerstuk ' + document_id + ' not found in database. Kamerstuk is probably not yet published.')
        elif dossiers[0].voting and dossiers[0].voting.date > voting_obj.date:  # A voting can be postponed and later voted on, we do not save the postponed voting if there is a newer voting
            logger.info('newer voting for this dossier already exits, skip this voting')
            continue
        elif dossiers[0].voting:
            dossiers[0].voting.delete()
        voting_obj.is_individual = voting_result.is_individual()
        voting_obj.save()
        if voting_obj.is_individual:
            create_votes_individual(voting_obj, voting_result.votes)
        else:
            create_votes_party(voting_obj, voting_result.votes)
    logger.info('END')


@transaction.atomic
def create_votes_party(voting, votes):
    logger.info('BEGIN')
    for vote in votes:
        party = PoliticalParty.find_party(vote.party_name)
        if not party:
            wikidata_id = wikidata.search_political_party_id(vote.party_name, language='nl')
            name = vote.party_name
            if wikidata_id:
                item = wikidata.WikidataItem(wikidata_id)
                name = item.get_label('nl')
            if not name:
                logger.error('vote party has no name')
                assert False
            party = PoliticalParty.objects.create(
                name=name,
                name_short=vote.party_name,
                wikidata_id=wikidata_id
            )
            party.update_info(language='nl')
        if not vote.decision:
            logger.warning('vote has no decision, vote.details: ' + str(vote.details))
        VoteParty.objects.create(
            voting=voting,
            party=party,
            party_name=vote.party_name,
            number_of_seats=vote.number_of_seats,
            decision=get_decision(vote.decision),
            details=vote.details,
            is_mistake=vote.is_mistake
        )
    logger.info('END')


@transaction.atomic
def create_votes_individual(voting, votes):
    logger.info('BEGIN')
    for vote in votes:
        initials, surname, surname_prefix = parse_name_surname_initials(vote.parliament_member)
        parliament_member = ParliamentMember.find(surname=surname, initials=initials)
        if not parliament_member:
            logger.error('parliament member not found for vote: ' + str(vote))
            logger.error('creating vote with empty parliament member')
            if voting.kamerstuk:
                logger.error('on kamerstuk: ' + str(voting.kamerstuk) + ', in dossier: ' + str(voting.kamerstuk.document.dossier) + ', for name: ' + surname + ' ' + initials)
            else:
                logger.error('voting.kamerstuk does not exist')
        VoteIndividual.objects.create(
            voting=voting,
            person_name=vote.parliament_member,
            parliament_member=parliament_member,
            number_of_seats=vote.number_of_seats,
            decision=get_decision(vote.decision),
            details=vote.details,
            is_mistake=vote.is_mistake
        )
    logger.info('END')


def get_result_choice(result_string):
    result_string = result_string.lower()
    if 'aangenomen' in result_string or 'overeenkomstig' in result_string:
        return Voting.AANGENOMEN
    elif 'verworpen' in result_string:
        return Voting.VERWORPEN
    elif 'ingetrokken' in result_string:
        return Voting.INGETROKKEN
    elif 'aangehouden' in result_string or 'uitgesteld' in result_string:
        return Voting.AANGEHOUDEN
    elif 'controversieel verklaard' in result_string:
        return Voting.CONTROVERSIEEL
    logger.error('could not interpret the voting result: ' + result_string)
    return Voting.ONBEKEND


def get_decision(decision_string):
    if scraper.votings.Vote.FOR == decision_string:
        return Vote.FOR
    elif scraper.votings.Vote.AGAINST == decision_string:
        return Vote.AGAINST
    elif scraper.votings.Vote.NOVOTE == decision_string:
        return Vote.NONE
    logger.error('no decision detected, returning Vote.NONE')
    return Vote.NONE


def create_besluitenlijsten(max_commissions=None, max_results_per_commission=None, skip_existing=False):
    logger.info('BEGIN')
    besluiten_lijsten = []
    commissies = scraper.besluitenlijst.get_voortouwcommissies_besluiten_urls()
    for index, commissie in enumerate(commissies):
        urls = scraper.besluitenlijst.get_besluitenlijsten_urls(commissie['url'], max_results=max_results_per_commission)
        for url in urls:
            if skip_existing and BesluitenLijst.objects.filter(url=url).exists():
                logger.info('besluitenlijst already exists, skip')
                continue
            try:
                besluiten_lijst = create_besluitenlijst(url)
                besluiten_lijsten.append(besluiten_lijst)
            except PDFSyntaxError as e:
                logger.error('failed to download and parse besluitenlijst with url: ' + url)
            except TypeError as e:
                # pdfminer error that may cause this has been reported here: https://github.com/euske/pdfminer/pull/89
                logger.error('error while converting besluitenlijst pdf to text')
                logger.error(traceback.format_exc())
            except:
                logger.error('failed to download and parse besluitenlijst with url: ' + url)
                logger.error(traceback.format_exc())
                raise
        if max_commissions and (index+1) >= max_commissions:
            break
    logger.info('END')
    return besluiten_lijsten


@transaction.atomic
def create_besluitenlijst(url):
    logger.info('BEGIN')
    logger.info('url: ' + url)
    filename = uuid.uuid4().hex + '.pdf'
    filepath = os.path.join(settings.OK_TMP_DIR, filename)
    with open(filepath, 'wb') as pdffile:
        response = requests.get(url, timeout=60)
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
