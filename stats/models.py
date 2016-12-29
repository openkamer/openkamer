import logging

from django.db import models
from django.db import transaction

from person.models import Person

from document.models import Vote
from document.models import VoteParty
from document.models import Voting

from government.models import Government
from parliament.models import PoliticalParty

from stats import util

logger = logging.getLogger(__name__)


def update_all():
    logger.info('BEGIN')
    StatsVotingSubmitter.create()
    PartyVoteBehaviour.create_all()
    logger.info('END')


class PartyVoteBehaviour(models.Model):
    BILL = 'BILL'
    OTHER = 'OTHER'
    VOTING_TYPE_CHOICES = (
        (BILL, 'Wetsvoorstel'),
        (OTHER, 'Overig (Motie, Amendement)')
    )
    party = models.ForeignKey(PoliticalParty)
    submitter = models.ForeignKey(PoliticalParty, related_name='party_vote_behaviour_submitter', blank=True, null=True)
    government = models.ForeignKey(Government)
    voting_type = models.CharField(max_length=5, choices=VOTING_TYPE_CHOICES)
    votes_for = models.IntegerField()
    votes_against = models.IntegerField()
    votes_none = models.IntegerField()

    def total_votes(self):
        return self.votes_for + self.votes_against + self.votes_none

    @staticmethod
    @transaction.atomic
    def create_all():
        logger.info('BEGIN')
        PartyVoteBehaviour.objects.all().delete()
        parties = PoliticalParty.objects.all()
        for party in parties:
            PartyVoteBehaviour.create(party)
        logger.info('END')

    @staticmethod
    @transaction.atomic
    def create(party):
        logger.info('BEGIN for party: ' + str(party))
        governments = Government.objects.all()
        party_votes_per_gov = []
        for gov in governments:
            party_votes_per_gov.append({'government': gov, 'party_votes': util.get_party_votes_for_government(gov)})
        stats = []
        parties = PoliticalParty.objects.all()
        for party_submitting in parties:
            PartyVoteBehaviour.create_for_submitting_party(party, party_submitting, party_votes_per_gov)
        PartyVoteBehaviour.create_for_submitting_party(party, None, party_votes_per_gov)
        logger.info('END')
        return stats

    @staticmethod
    def create_for_submitting_party(party, party_submitting, party_votes_per_gov):
        for votes_for_gov in party_votes_per_gov:
            for voting_type in PartyVoteBehaviour.VOTING_TYPE_CHOICES:
                PartyVoteBehaviour.create_party_type_gov(
                    party=party,
                    party_votes=votes_for_gov['party_votes'],
                    party_submitting=party_submitting,
                    government=votes_for_gov['government'],
                    voting_type=voting_type[0]
                )

    @staticmethod
    def create_party_type_gov(party, party_votes, party_submitting, government, voting_type):
        if voting_type == PartyVoteBehaviour.BILL:
            party_votes = party_votes.filter(voting__is_dossier_voting=True)
        elif voting_type == PartyVoteBehaviour.OTHER:
            party_votes = party_votes.filter(voting__is_dossier_voting=False)
        else:
            assert False
        party_votes = party_votes.filter(party=party)
        if party_submitting is not None:
            voting_ids = PartyVoteBehaviour.get_voting_ids_submitted_by_party(party_submitting)
            party_votes = party_votes.filter(voting__in=voting_ids).distinct()
        votes_for = party_votes.filter(decision=Vote.FOR)
        votes_against = party_votes.filter( decision=Vote.AGAINST)
        votes_none = party_votes.filter(decision=Vote.NONE)
        PartyVoteBehaviour.objects.create(
            party=party,
            submitter=party_submitting,
            government=government,
            voting_type=voting_type,
            votes_for=votes_for.count(),
            votes_against=votes_against.count(),
            votes_none=votes_none.count()
        )

    @staticmethod
    def get_voting_ids_submitted_by_party(party):
        submitters = StatsVotingSubmitter.objects.filter(party=party).select_related('voting')
        voting_ids = set()
        for submitter in submitters:
            voting_ids.add(submitter.voting.id)
        return voting_ids


class StatsVotingSubmitter(models.Model):
    voting = models.ForeignKey(Voting)
    person = models.ForeignKey(Person)
    party = models.ForeignKey(PoliticalParty, blank=True, null=True)

    @staticmethod
    @transaction.atomic
    def create():
        logger.info('BEGIN')
        StatsVotingSubmitter.objects.all().delete()
        votings = Voting.objects.all()
        for voting in votings:
            for submitter in voting.submitters:
                StatsVotingSubmitter.objects.create(
                    voting=voting,
                    person=submitter.person,
                    party=submitter.party
                )
        logger.info('END')
