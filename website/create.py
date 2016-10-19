import logging
import re

from wikidata import wikidata

from person.models import Person

from government.models import Government
from government.models import Ministry
from government.models import GovernmentPosition
from government.models import GovernmentMember

from parliament.models import PoliticalParty
from parliament.models import ParliamentMember
from parliament.util import parse_name_initials_surname
from parliament.util import parse_name_surname_initials

from document.models import Agenda
from document.models import AgendaItem
from document.models import Document
from document.models import Dossier
from document.models import Kamerstuk
from document.models import Submitter
from document.models import Voting
from document.models import Vote
from document.models import VoteParty
from document.models import VoteIndividual

import scraper.government
import scraper.documents
import scraper.votings

logger = logging.getLogger(__name__)


def create_governments():
    # Rutte II : Q1638648
    government_ids = ['Q1638648']
    for gov_id in government_ids:
        gov_info = scraper.government.get_government(gov_id)
        government, created = Government.objects.get_or_create(
            name=gov_info['name'],
            date_formed=gov_info['inception'],
            wikidata_id=gov_id
        )
        create_government_members(government)


def create_government_members(government):
    members = scraper.government.get_government_members(government.wikidata_id)
    for member in members:
        ministry = None
        if 'ministry' in member:
            ministry, created = Ministry.objects.get_or_create(name=member['ministry'].lower(), government=government)
        position = GovernmentPosition.objects.create(ministry=ministry, position=GovernmentPosition.find_position_type(member['position']))
        forename = wikidata.get_given_name(member['wikidata_id'])
        surname = member['name'].replace(forename, '').strip()
        prefix = Person.find_prefix(surname)
        if prefix:
            surname = surname.replace(prefix + ' ', '')
        person = Person.objects.create(
            forename=forename,
            surname=surname,
            surname_prefix=prefix,
            wikidata_id=member['wikidata_id']
        )
        start_date = government.date_formed
        if 'start_date' in member:
            start_date = member['start_date']
        end_date = None
        if 'end_date' in member:
            end_date = member['end_date']
        GovernmentMember.objects.get_or_create(
            person=person,
            position=position,
            start_date=start_date,
            end_date=end_date
        )


def create_or_update_dossier(dossier_id):
    # TODO: do not create new documents if they already exist; update!
    logger.info('BEGIN - dossier id: ' + str(dossier_id))
    dossiers = Dossier.objects.filter(dossier_id=dossier_id)
    if dossiers:
        dossier = dossiers[0]
    else:
        dossier = Dossier.objects.create(dossier_id=dossier_id)
    search_results = scraper.documents.search_politieknl_dossier(dossier_id)
    for result in search_results:
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


def create_kamerstuk(document, dossier_id, metadata, result):
    logger.info('BEGIN')
    logger.info('document: ' + str(document))
    title_parts = metadata['title_full'].split(';')
    type_short = ''
    type_long = ''
    original_id = ''
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
        return main_id + '.' + sub_id
    elif sub_id:
        return str(dossier_id) + '.' + sub_id
    elif 'voorstel van wet' in type_long.lower():
        return str(dossier_id) + '.voorstel_van_wet'
    return ''


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


def create_votings(dossier_id):
    logger.info('dossier id: ' + str(dossier_id))
    voting_results = scraper.votings.get_votings_for_dossier(dossier_id)
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


def create_votes_party(voting, votes):
    for vote in votes:
        party = PoliticalParty.find_party(vote.party_name)
        assert party
        VoteParty.objects.create(voting=voting, party=party, number_of_seats=vote.number_of_seats,
                                 decision=get_decision(vote.decision), details=vote.details)


def create_votes_individual(voting, votes):
    for vote in votes:
        initials, surname = parse_name_surname_initials(vote.parliament_member)
        parliament_member = ParliamentMember.find(surname=surname, initials=initials)
        if not parliament_member:
            logger.error('parliament member not found for vote: ' + str(vote))
            if voting.kamerstuk:
                logger.error('on kamerstuk: ' + str(voting.kamerstuk) + ', in dossier: ' + str(voting.kamerstuk.document.dossier) + ', for name: ' + surname + ' ' + initials)
            else:
                logger.error('voting.kamerstuk does not exist')
            assert False
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