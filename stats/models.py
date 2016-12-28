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
    StatsVotingSubmitter.create()
    PartyVoteBehaviour.create_all()


class PartyVoteBehaviour(models.Model):
    BILL = 'BILL'
    OTHER = 'OTHER'
    VOTING_TYPE_CHOICES = (
        (BILL, 'Wetsvoorstel'),
        (OTHER, 'Overig (Motie, Amendement)')
    )
    party = models.ForeignKey(PoliticalParty)
    submitter = models.ForeignKey(PoliticalParty, related_name='party_vote_behaviour_submitter')
    government = models.ForeignKey(Government)
    voting_type = models.CharField(max_length=5, choices=VOTING_TYPE_CHOICES, blank=True, null=True)
    votes_for = models.IntegerField()
    votes_against = models.IntegerField()
    votes_none = models.IntegerField()

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
        parties = PoliticalParty.objects.all()
        governments = Government.objects.all()
        party_votes_per_gov = []
        for gov in governments:
            party_votes_per_gov.append({
                'government': gov,
                'party_votes': util.get_party_votes_for_government(gov)
            })
        stats = []
        for party_submitting in parties:
            for votes_for_gov in party_votes_per_gov:
                for voting_type in PartyVoteBehaviour.VOTING_TYPE_CHOICES:
                    PartyVoteBehaviour.create_party_type_gov(party, party_submitting, votes_for_gov, voting_type[0])
        logger.info('END')
        return stats

    @staticmethod
    def create_party_type_gov(party, party_submitting, votes_for_gov, voting_type):
        party_votes = votes_for_gov['party_votes']
        if voting_type == PartyVoteBehaviour.BILL:
            party_votes = party_votes.filter(voting__is_dossier_voting=True)
        elif voting_type == PartyVoteBehaviour.OTHER:
            party_votes = party_votes.filter(voting__is_dossier_voting=False)
        party_votes = party_votes.distinct()
        party_votes = party_votes.filter(party=party)
        voting_ids = PartyVoteBehaviour.get_voting_ids_submitted_by_party(party_submitting)
        party_votes = party_votes.filter(voting__in=voting_ids).distinct()
        votes_for = party_votes.filter(party=party, decision=Vote.FOR)
        votes_against = party_votes.filter(party=party, decision=Vote.AGAINST)
        votes_none = party_votes.filter(party=party, decision=Vote.NONE)
        PartyVoteBehaviour.objects.create(
            party=party,
            submitter=party_submitting,
            government=votes_for_gov['government'],
            voting_type=voting_type,
            votes_for=votes_for.count(),
            votes_against=votes_against.count(),
            votes_none=votes_none.count()
        )

    @staticmethod
    def get_voting_ids_submitted_by_party(party):
        if party is None:
            submitters = StatsVotingSubmitter.objects.all().select_related('voting')
        else:
            submitters = StatsVotingSubmitter.objects.filter(party=party).select_related('voting')
        voting_ids = []
        for submitter in submitters:
            voting_ids.append(submitter.voting.id)
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
