import datetime
import logging

from django.db import transaction

from wikidata import wikidata

import scraper.votings

from person.util import parse_name_surname_initials

from parliament.models import ParliamentMember
from parliament.models import PoliticalParty

from document.models import Dossier
from document.models import Kamerstuk
from document.models import Vote
from document.models import VoteIndividual
from document.models import VoteParty
from document.models import Voting


logger = logging.getLogger(__name__)


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
