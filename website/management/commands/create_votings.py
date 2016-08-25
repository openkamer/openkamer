from django.core.management.base import BaseCommand

import scraper.votings
import voting.models

from parliament.models import PoliticalParty
from document.models import Dossier
from document.models import Kamerstuk


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('dossier_id', nargs='+', type=int)

    def handle(self, *args, **options):
        # dossier_id = 33885
        dossier_id = options['dossier_id'][0]
        voting_results = scraper.votings.get_votings_for_dossier(dossier_id)
        for voting_result in voting_results:
            result = self.get_result_choice(voting_result.get_result())
            if result is None:
                print('ERROR: Could not interpret vote result: ' + voting_result.get_result())
                assert False
            document_id = voting_result.get_document_id()
            id_main = document_id.split('-')[0]
            dossiers = Dossier.objects.filter(dossier_id=id_main)
            voting_obj = voting.models.Voting(dossier=dossiers[0], date=voting_result.date, result=result)
            assert dossiers.count() == 1
            if len(document_id.split('-')) == 2:
                id_sub = document_id.split('-')[1]
                kamerstukken = Kamerstuk.objects.filter(id_main=id_main, id_sub=id_sub)
                voting_obj.kamerstuk = kamerstukken[0]
            voting_obj.save()
            for vote in voting_result.votes:
                party = PoliticalParty.find_party(vote.party_name)
                assert party
                voting.models.Vote.objects.create(voting=voting_obj, party=party, number_of_seats=vote.number_of_seats, decision=self.get_decision(vote.decision), details=vote.details)

    @staticmethod
    def get_result_choice(result_string):
        if 'aangenomen' in result_string.lower():
            return voting.models.Voting.AANGENOMEN
        elif 'verworpen' in result_string.lower():
            return voting.models.Voting.VERWORPEN
        elif 'ingetrokken' in result_string.lower():
            return voting.models.Voting.INGETROKKEN
        elif 'aangehouden' in result_string.lower():
            return voting.models.Voting.AANGEHOUDEN
        return None

    @staticmethod
    def get_decision(decision_string):
        if 'for' in decision_string.lower():
            return voting.models.Vote.FOR
        elif 'against' in decision_string.lower():
            return voting.models.Vote.AGAINST
        return None



