import datetime
import logging
from typing import List
import urllib.parse

from requests.exceptions import ConnectionError, ConnectTimeout, ChunkedEncodingError

from json.decoder import JSONDecodeError

from django.db import transaction

from wikidata import wikidata
import wikidata.government as wikidata_government

import tkapi
from tkapi.fractie import Fractie
from tkapi.persoon import Persoon as TKPersoon

import scraper.persons

from person.models import Person

from government.models import Government
from government.models import GovernmentMember
from government.models import GovernmentPosition
from government.models import Ministry

from parliament.models import Parliament
from parliament.models import ParliamentMember
from parliament.models import PartyMember
from parliament.models import PoliticalParty

from document.models import VoteIndividual
from document.models import VoteParty

import stats.models


logger = logging.getLogger(__name__)


@transaction.atomic
def create_parliament_and_government(all_members=False):
    PoliticalParty.objects.all().delete()
    PartyMember.objects.all().delete()
    ParliamentMember.objects.all().delete()
    create_parties(update_votes=False)
    create_governments()
    create_parliament_members(update_votes=False, all_members=all_members)
    for party in PoliticalParty.objects.all():
        party.set_current_parliament_seats()
    set_party_votes_derived_info()
    set_individual_votes_derived_info()
    Person.update_persons_all(language='nl')
    stats.models.update_all()


@transaction.atomic
def create_governments():
    # Kabinet-Balkenende III : Q1473297
    # Balkenende IV : Q1719725
    # Rutte I : Q168828
    # Rutte II : Q1638648
    # Rutte III : Q42293409
    government_ids = ['Q42293409', 'Q1638648', 'Q168828', 'Q1719725', 'Q1473297']
    for wikidata_id in government_ids:
        create_government(wikidata_id)


@transaction.atomic
def create_government(wikidata_id, max_members=None):
    gov_info = wikidata_government.get_government(wikidata_id)
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
    members = wikidata_government.get_government_members(government.wikidata_id, max_members=max_members)
    for member in members:
        if 'position' not in member:
            logger.error('no position found for government member: ' + member['name'] + ' with wikidata id: ' + member['wikidata_id'])
            continue
        logger.info(member['name'] + ' ' + member['position'])
        ministry = create_ministry(government, member)
        position = create_government_position(government, member, ministry)
        person = get_or_create_person(member['wikidata_id'], member['name'], add_initials=True)
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
def create_parties(update_votes=True, active_only=False) -> List[PoliticalParty]:
    filter_fractie = None
    if active_only:
        filter_fractie = Fractie.create_filter()
        filter_fractie.filter_actief()
    api = tkapi.Api()
    fracties = api.get_fracties(filter=filter_fractie)
    parties = []
    for fractie in fracties:
        party = create_party(fractie.naam, fractie.afkorting)
        parties.append(party)
    if update_votes:
        set_party_votes_derived_info()
    return parties


@transaction.atomic
def create_party(name, name_short):
    party = PoliticalParty.find_party(name)
    if party:
        party.delete()
    party = PoliticalParty.objects.create(name=name, name_short=name_short)
    party.update_info(language='nl')
    return party


@transaction.atomic
def create_party_wikidata(wikidata_id):
    wikidata_party_item = wikidata.WikidataItem(wikidata_id)
    name = wikidata_party_item.get_label(language='nl')
    name_short = wikidata_party_item.get_short_name(language='nl')
    if not name_short:
        name_short = name
    party = create_party(name=name, name_short=name_short)
    return party


@transaction.atomic
def create_party_members():
    logger.info('BEGIN')
    persons = Person.objects.filter(wikidata_id__isnull=False).order_by('surname')
    for person in persons:
        create_party_members_for_person(person)
    logger.info('END')


@transaction.atomic
def create_party_members_for_person(person):
    logger.info('BEGIN, person: ' + str(person))
    if not person.wikidata_id:
        logger.warning('could not update party member for person: ' + str(person) + ' because person has no wikidata id.')
        return
    wikidata_person_item = wikidata.WikidataItem(person.wikidata_id)
    memberships = wikidata_person_item.get_political_party_memberships()
    for membership in memberships:
        parties = PoliticalParty.objects.filter(wikidata_id=membership['party_wikidata_id'])
        if parties.exists():
            party = parties[0]
        else:
            party = create_party_wikidata(membership['party_wikidata_id'])
        PartyMember.objects.create(
            person=person,
            party=party,
            joined=membership['start_date'],
            left=membership['end_date']
        )
    logger.info('END')


@transaction.atomic
def create_parliament_members(max_results=None, all_members=False, update_votes=True):
    logger.info('BEGIN')
    parliament = Parliament.get_or_create_tweede_kamer()
    if all_members:
        member_wikidata_ids = wikidata.search_parliament_member_ids()
    else:
        member_wikidata_ids = wikidata.search_parliament_member_ids_with_start_date()
    counter = 0
    members = []
    for person_wikidata_id in member_wikidata_ids:
        logger.info('=========================')
        try:
            members += create_parliament_member_from_wikidata_id(parliament, person_wikidata_id)
        except (JSONDecodeError, ConnectionError, ConnectTimeout, ChunkedEncodingError) as error:
            logger.exception(error)
        except Exception as error:
            logger.exception(error)
            raise
        counter += 1
        if max_results and counter >= max_results:
            logger.info('END: max results reached')
            break
    if update_votes:
        set_individual_votes_derived_info()
    logger.info('END')
    return members


def create_parliament_member_from_wikidata_id(parliament, person_wikidata_id):
    wikidata_item = wikidata.WikidataItem(person_wikidata_id)
    person = get_or_create_person(person_wikidata_id, wikidata_item=wikidata_item, add_initials=True)
    logger.info(person)
    positions = wikidata_item.get_parliament_positions_held()
    members = []
    for position in positions:
        parliament_member = ParliamentMember.objects.create(
            person=person,
            parliament=parliament,
            joined=position['start_time'],
            left=position['end_time']
        )
        logger.info(parliament_member)
        members.append(parliament_member)
        if position['part_of_id']:
            party_item = wikidata.WikidataItem(position['part_of_id'])
            parties = PoliticalParty.objects.filter(wikidata_id=position['part_of_id'])
            if parties:
                party = parties[0]
            else:
                party = PoliticalParty.find_party(party_item.get_label(language='nl'))
            if not party:
                party = create_party_wikidata(wikidata_id=position['part_of_id'])
            PartyMember.objects.create(person=person, party=party, joined=position['start_time'], left=position['end_time'])
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
def get_or_create_person(wikidata_id, fullname='', wikidata_item=None, add_initials=False):
    if not wikidata_item:
        wikidata_item = wikidata.WikidataItem(wikidata_id)
    persons = Person.objects.filter(wikidata_id=wikidata_id)
    if persons.count() > 1:
        logger.warning('more than one person with same wikidata_id found, wikidata id: ' + str(wikidata_id))
    if persons.count() == 1:
        person = persons[0]
    else:
        person = create_person(wikidata_id, fullname, wikidata_item, add_initials)
    party_members = PartyMember.objects.filter(person=person)
    if not party_members.exists():
        create_party_members_for_person(person)
    return person


def create_person(wikidata_id, fullname, wikidata_item, add_initials):
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
    add_tk_person_id(person)
    assert person.wikidata_id == wikidata_id
    return person


def add_tk_person_id(person: Person) -> Person:
    tkperson = find_tkapi_person(person)
    if tkperson:
        person.tk_id = tkperson.id
        person.save()
    return person


def find_tkapi_person(person: Person) -> TKPersoon or None:
    # TODO BR: cleanup: this is a mess!
    filter = TKPersoon.create_filter()
    filter.filter_achternaam(person.surname)
    try:
        persons = tkapi.Api().get_personen(filter=filter)
        if not persons:
            persons = []
            surname_parts = person.surname.split('-')
            surname_parts += person.surname.split(' ')
            for part in surname_parts:
                filter = TKPersoon.create_filter()
                filter.filter_achternaam(part)
                persons += tkapi.Api().get_personen(filter=filter)
    except KeyError:
        logger.exception('Could not find TK Person for {} ({})'.format(person.surname, person.initials))
        return None
    surname_matches = [tkperson for tkperson in persons if tkperson.achternaam.lower() == person.surname.lower()]
    if len(surname_matches) == 1:
        return surname_matches[0]
    if len(surname_matches) == 0:
        surname_parts = person.surname.split('-')
        surname_parts += person.surname.split(' ')
        surname_parts = [surname.lower() for surname in surname_parts]
        tk_surname_parts = []
        surname_matches = []
        for tkperson in persons:
            tk_surname_parts += tkperson.achternaam.split('-')
            tk_surname_parts += tkperson.achternaam.split(' ')
            tk_surname_parts = [surname.lower() for surname in tk_surname_parts]
            for tk_part in tk_surname_parts:
                if tk_part in surname_parts:
                    surname_matches.append(tkperson)
    if len(surname_matches) == 1:
        return surname_matches[0]
    for tkperson in surname_matches:
        if tkperson.initialen.lower() == person.initials.lower():
            return tkperson
        elif tkperson.initialen.replace('.', '').lower() == person.initials.replace('.', '').lower():
            return tkperson
    if surname_matches:
        return surname_matches[0]
    return None


@transaction.atomic
def update_initials():
    persons = Person.objects.all()
    for person in persons:
        person.initials = scraper.persons.get_initials(person.parlement_and_politiek_id)
        person.save()


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
