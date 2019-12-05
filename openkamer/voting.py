import logging

from django.db import transaction

from wikidata import wikidata

from tkapi.util import queries
from tkapi.zaak import ZaakSoort
from person.util import parse_name_surname_initials

from person.models import Person
from parliament.models import ParliamentMember
from parliament.models import PoliticalParty

from document.models import Dossier
from document.models import Kamerstuk
from document.models import Vote
from document.models import VoteIndividual
from document.models import VoteParty
from document.models import Voting


logger = logging.getLogger(__name__)


def clean_voting_results(voting_results, dossier_id):
    """ Removes votings for other dossiers and duplicate controversial dossier votings """
    voting_results_cleaned = []
    for voting_result in voting_results:
        if str(voting_result.get_dossier_id()) != str(dossier_id):
            # this should only happen for controversial voting result lists, example: https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2017P05310
            logger.info('Voting for different dossier, remove voting')
            continue
        voting_results_cleaned.append(voting_result)
    return voting_results_cleaned


class VotingFactory(object):

    def __init__(self, do_create_missing_party=True):
        self.vote_factory = VoteFactory(do_create_missing_party=do_create_missing_party)

    @transaction.atomic
    def create_votings(self, dossier_id):
        logger.info('BEGIN')
        logger.info('dossier id: ' + str(dossier_id))
        dossier_id_main, dossier_id_sub = Dossier.split_dossier_id(dossier_id)
        besluiten = queries.get_dossier_besluiten_with_stemmingen(nummer=dossier_id_main, toevoeging=dossier_id_sub)
        for besluit in besluiten:
            self.create_votings_dossier_besluit(besluit, dossier_id)
        logger.info('END')

    @transaction.atomic
    def create_votings_dossier_besluit(self, besluit, dossier_id):
        dossiers = Dossier.objects.filter(dossier_id=dossier_id)
        assert dossiers.count() == 1
        dossier = dossiers[0]
        result = self.get_result_choice(besluit.tekst)
        zaak = besluit.zaak

        document_id = ''
        if zaak.volgnummer:
            document_id = str(dossier_id) + '-' + str(zaak.volgnummer)

        is_dossier_voting = zaak.soort in [ZaakSoort.WETGEVING, ZaakSoort.INITIATIEF_WETGEVING, ZaakSoort.BEGROTING]
        is_dossier_voting = is_dossier_voting or str(zaak.volgnummer) == '0'
        logger.info('{} | dossier voting: {}'.format(document_id, is_dossier_voting))
        voting_obj = Voting(
            dossier=dossier,
            kamerstuk_raw_id=document_id,
            result=result,
            date=besluit.agendapunt.activiteit.begin.date(),  # TODO BR: replace with besluit date
            source_url='',
            is_dossier_voting=is_dossier_voting
        )

        kamerstukken = Kamerstuk.objects.filter(id_main=dossier_id, id_sub=zaak.volgnummer)
        if kamerstukken.exists():
            kamerstuk = kamerstukken[0]
            voting_obj.kamerstuk = kamerstuk
            # A voting can be postponed and later voted on
            # we do not save the postponed voting if there is a newer voting
            if kamerstuk.voting and kamerstuk.voting.date > voting_obj.date:
                logger.info('newer voting for this kamerstuk already exits, skip this voting')
                return
            elif kamerstuk.voting:
                kamerstuk.voting.delete()
        elif not is_dossier_voting:
            logger.error(
                'Kamerstuk ' + document_id + ' not found in database. Kamerstuk is probably not yet published.')

        voting_obj.is_individual = ('hoofdelijk' in besluit.tekst.lower())
        voting_obj.save()

        if voting_obj.is_individual:
            self.vote_factory.create_votes_individual(voting_obj, besluit.stemmingen)
        else:
            self.vote_factory.create_votes_party(voting_obj, besluit.stemmingen)

    @staticmethod
    def get_result_choice(result_string):
        result_string = result_string.lower()
        result_string.replace('.', '')
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


class VoteFactory(object):

    def __init__(self, do_create_missing_party=True):
        self.do_create_missing_party = do_create_missing_party

    @transaction.atomic
    def create_votes_party(self, voting, stemmingen):
        logger.info('BEGIN')
        for stemming in stemmingen:
            fractie_name = stemming.actor_fractie if stemming.actor_fractie else stemming.actor_naam
            party = PoliticalParty.find_party(fractie_name)
            if not party and self.do_create_missing_party:
                party = self.create_missing_party(stemming)
            if not stemming.soort:
                logger.warning('vote has no decision, vote.details: ' + str(stemming.soort))
            VoteParty.objects.create(
                voting=voting,
                party=party,
                party_name=fractie_name,
                number_of_seats=stemming.fractie_size,
                decision=self.get_decision(stemming.soort),
                details='',
                is_mistake=stemming.vergissing if stemming.vergissing is not None else False
            )
        logger.info('END')

    @staticmethod
    def create_missing_party(stemming):
        party_name = stemming.actor_naam  # TODO: use fractie.naam (currently not available in TK API)
        wikidata_id = wikidata.search_political_party_id(party_name, language='nl')
        party = PoliticalParty.objects.create(
            name=party_name,
            # name_short=stemming.fractie.afkorting, # TODO: use fractie.afkorting (currently not available in TK API)
            wikidata_id=wikidata_id
        )
        party.update_info(language='nl')
        return party

    @transaction.atomic
    def create_votes_individual(self, voting, stemmingen):
        logger.info('BEGIN')
        for stemming in stemmingen:
            persoon = stemming.persoon
            parliament_member = None

            persons = Person.objects.filter(tk_id=persoon.id)
            if persons:
                person = persons[0]
                members = ParliamentMember.objects.filter(person=person).order_by('-joined')
                parliament_member = members[0] if members.exists() else None
                person_name = ' '.join([person.surname, person.surname, person.initials]).strip()

            # TODO BR: this is a fallback, remove or extract function and log
            if parliament_member is None:
                if persoon:
                    initials = persoon.initialen
                    surname = persoon.achternaam
                    forname = persoon.roepnaam
                else:
                    logger.error('Persoon not found for stemming: ' + stemming.id)
                    surname_initials = stemming.json['AnnotatieActorNaam']
                    forname = ''
                    initials, surname, surname_prefix = parse_name_surname_initials(surname_initials)

                parliament_member = ParliamentMember.find(surname=surname, initials=initials)
                if not parliament_member:
                    logger.error('parliament member not found for vote: ' + str(stemming.id))
                    logger.error('creating vote with empty parliament member')
                person_name = ' '.join([forname, surname, initials]).strip()

            VoteIndividual.objects.create(
                voting=voting,
                person_name=person_name,
                parliament_member=parliament_member,
                number_of_seats=1,
                decision=self.get_decision(stemming.soort),
                details='',
                is_mistake=stemming.vergissing if stemming.vergissing is not None else False
            )
        logger.info('END')

    @staticmethod
    def get_decision(decision_string):
        if 'Voor' == decision_string:
            return Vote.FOR
        elif 'Tegen' == decision_string:
            return Vote.AGAINST
        elif 'Niet deelgenomen' == decision_string:
            return Vote.NONE
        logger.error('no decision detected, returning Vote.NONE')
        return Vote.NONE



