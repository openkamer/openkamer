import logging
from typing import List

from requests.exceptions import ConnectionError, ConnectTimeout, ChunkedEncodingError

from json.decoder import JSONDecodeError

from django.db import transaction

from wikidata import wikidata
from wikidata.government import GovernmentMemberData
import wikidata.government as wikidata_government

import tkapi
from tkapi.fractie import Fractie as TKFractie
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
    # Rutte IV : Q110111120
    # Schoof: Q126527270
    government_ids = ['Q126527270', 'Q110111120', 'Q42293409', 'Q1638648', 'Q168828', 'Q1719725', 'Q1473297']
    for wikidata_id in government_ids:
        create_government(wikidata_id)


@transaction.atomic
def create_government(wikidata_id, max_members=None):
    logger.info('BEGIN: {}'.format(wikidata_id))
    gov_info = wikidata_government.get_government(wikidata_id)
    Government.objects.filter(wikidata_id=wikidata_id).delete()
    government = Government.objects.create(
        name=gov_info['name'],
        date_formed=gov_info['start_date'],
        date_dissolved=gov_info['end_date'],
        wikidata_id=wikidata_id
    )
    create_government_members(government, max_members=max_members)
    logger.info('END: {}'.format(wikidata_id))
    return government


@transaction.atomic
def create_government_members(government, max_members=None):
    members_created = []
    members = wikidata_government.get_government_members(government.wikidata_id, max_members=max_members)
    for member in members:
        if member.position is None:
            logger.error('no position found for government member: {} ({})'.format(member.name, member.wikidata_id))
            continue
        logger.info('{} | {} | {}'.format(member.name, member.position, member.ministry))
        ministry = create_ministry(government, member)
        if ministry is None:
            logger.warning('No ministry found for government member: {} ({})'.format(member.name, member.wikidata_id))
        position = create_government_position(government, member, ministry)
        person = get_or_create_person(member.wikidata_id, member.name, add_initials=True)
        gov_member = create_goverment_member(government, member, person, position)
        members_created.append(gov_member)
    return members_created


@transaction.atomic
def create_ministry(government, member: GovernmentMemberData):
    ministry = None
    if member.ministry:
        ministry, created = Ministry.objects.get_or_create(name=member.ministry.lower(), government=government)
    return ministry


@transaction.atomic
def create_goverment_member(government, member: GovernmentMemberData, person, position):
    start_date = member.start_date if member.start_date else government.date_formed
    end_date = member.end_date if member.end_date else government.date_dissolved
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
        filter_fractie = TKFractie.create_filter()
        filter_fractie.filter_actief()
    tk_fracties = tkapi.TKApi.get_fracties(filter=filter_fractie)
    parties = []
    for tk_fractie in tk_fracties:
        party = create_party(tk_fractie.naam, tk_fractie.afkorting, tk_fractie.id)
        parties.append(party)
    if update_votes:
        set_party_votes_derived_info()
    return parties


@transaction.atomic
def create_party(name, name_short, tk_id=None):
    party = PoliticalParty.find_party(name)
    if party:
        party.delete()
    party = PoliticalParty.objects.create(tk_id=tk_id, name=name, name_short=name_short)
    party.update_info(language='nl')
    return party


@transaction.atomic
def create_party_wikidata(wikidata_id):
    wikidata_party_item = wikidata.WikidataItem(wikidata_id)
    name = wikidata_party_item.get_label(language='nl')
    name_short = wikidata_party_item.get_short_name(language='nl')
    if not name_short:
        name_short = name
    filter_fractie = TKFractie.create_filter()
    filter_fractie.filter_fractie(naam=name)
    tk_fracties = tkapi.TKApi.get_fracties(filter=filter_fractie)
    tk_fractie_id = tk_fracties[0].id if tk_fracties else None
    party = create_party(name=name, name_short=name_short, tk_id=tk_fractie_id)
    return party


@transaction.atomic
def create_party_members_for_person(person: Person):
    logger.info('BEGIN - person: {}'.format(person))
    if not person.wikidata_id:
        logger.warning('could not update party member for person: {} because person has no wikidata id.'.format(person))
        return
    wikidata_person_item = wikidata.WikidataItem(person.wikidata_id)
    memberships = wikidata_person_item.get_political_party_memberships()
    PartyMember.objects.filter(person=person).delete()
    for membership in memberships:
        wikidata_party = wikidata.WikidataItem(membership['party_wikidata_id'])
        if wikidata_party.is_local_party or wikidata_party.is_youth_party:
            continue
        parties = PoliticalParty.objects.filter(wikidata_id=wikidata_party.id)
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
    person.tk_id = tkperson.id if tkperson else ''
    person.save()
    return person


def find_tkapi_person(person: Person) -> TKPersoon or None:
    # TODO BR: cleanup: this is a mess!
    filter = TKPersoon.create_filter()
    filter.filter_achternaam(person.surname)
    try:
        persons = tkapi.TKApi.get_personen(filter=filter)
        if not persons:
            persons = []
            surname_parts = person.surname.split('-')
            surname_parts += person.surname.split(' ')
            for part in surname_parts:
                filter = TKPersoon.create_filter()
                filter.filter_achternaam(part)
                persons += tkapi.TKApi.get_personen(filter=filter)
    except KeyError:
        logger.exception('Could not find TK Person for {} ({})'.format(person.surname, person.initials))
        return None

    surname_matches = [tkperson for tkperson in persons if tkperson.achternaam.lower() == person.surname.lower()]

    if len(surname_matches) == 0:
        surname_parts = person.surname.split('-')
        surname_parts += person.surname.split(' ')
        surname_parts = [surname.lower() for surname in surname_parts if len(surname) > 3]
        surname_matches = []
        for tkperson in persons:
            tk_surname_parts = []
            tk_surname_parts += tkperson.achternaam.split('-')
            tk_surname_parts += tkperson.achternaam.split(' ')
            tk_surname_parts = [surname.lower() for surname in tk_surname_parts if len(surname) > 3]
            for tk_part in tk_surname_parts:
                if tk_part in surname_parts:
                    surname_matches.append(tkperson)

    initial_matches = []
    for tkperson in surname_matches:
        if initials_equal(tkperson.initialen, person.initials):
            initial_matches.append(tkperson)

    for tkperson in initial_matches:
        if forename_almost_equal(person, tkperson):
            return tkperson

    for tkperson in surname_matches:
        if forename_almost_equal(person, tkperson):
            return tkperson

    return None


def forename_almost_equal(person, tkperson) -> bool:
    if not person.forename or not tkperson.voornamen:
        return False
    if tkperson.voornamen.lower() in person.forename.lower():
        return True
    if person.forename.lower() in tkperson.voornamen.lower():
        return True
    if person.forename.lower() in tkperson.roepnaam.lower():
        return True
    return False


def initials_equal(initials_a: str, initials_b) -> bool:
    initials_a = initials_a.lower()
    initials_b = initials_b.lower()
    if initials_a == '' or initials_b == '':
        return False
    if initials_a == initials_b:
        return True
    elif initials_a.replace('.', '') == initials_b.replace('.', ''):
        return True
    return False


@transaction.atomic
def update_initials():
    persons = Person.objects.all()
    for person in persons:
        person.initials = scraper.persons.get_initials(person.parlement_and_politiek_id)
        person.save()


@transaction.atomic
def create_government_position(government, member: GovernmentMemberData, ministry):
    position_type = GovernmentPosition.find_position_type(member.position)
    positions = GovernmentPosition.objects.filter(
        ministry=ministry,
        position=position_type,
        government=government,
        extra_info=member.position_name,
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
            extra_info=member.position_name,
        )
    return position
