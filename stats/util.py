import logging

from document.models import Vote
from document.models import VoteParty

from government.models import Government
from parliament.models import PoliticalParty

logger = logging.getLogger(__name__)


def get_party_votes_for_government(government, vote_party_qs=None):
    logger.info('BEGIN')
    if vote_party_qs is not None:
        votes_party = vote_party_qs.filter(voting__date__gte=government.date_formed)
    else:
        votes_party = VoteParty.objects.filter(voting__date__gte=government.date_formed)
    if government.date_dissolved:
        votes_party = votes_party.filter(voting__date__lt=government.date_dissolved)
    logger.info('END')
    return votes_party


def get_voting_stats_per_party(vote_party_qs):
    logger.info('BEGIN')
    vote_party_qs = vote_party_qs.select_related('voting')
    parties = PoliticalParty.objects.all()
    parties = PoliticalParty.sort_by_current_seats(parties)
    governments = Government.objects.all()
    party_votes_per_gov = []
    for gov in governments:
        party_votes_per_gov.append({
            'government': gov,
            'party_votes': get_party_votes_for_government(gov, vote_party_qs=vote_party_qs)
        })
    stats = []
    for party in parties:
        periods = []
        for votes_for_gov in party_votes_per_gov:
            party_votes = votes_for_gov['party_votes']
            votes_for = party_votes.filter(party=party, decision=Vote.FOR)
            votes_against = party_votes.filter(party=party, decision=Vote.AGAINST)
            votes_none = party_votes.filter(party=party, decision=Vote.NONE)
            n_votes = party_votes.filter(party=party).count()
            n_for = votes_for.count()
            n_against = votes_against.count()
            n_none = votes_none.count()
            if n_votes == 0:
                for_percent = 0
                against_percent = 0
                none_percent = 0
            else:
                for_percent = n_for/n_votes*100.0
                against_percent = n_against/n_votes*100.0
                none_percent = n_none/n_votes*100.0
            period = {
                'government': votes_for_gov['government'],
                'n_votes': n_votes,
                'n_for': n_for,
                'n_against': n_against,
                'n_none': n_none,
                'for': votes_for,
                'against': votes_against,
                'none': votes_none,
                'for_percent': for_percent,
                'against_percent': against_percent,
                'none_percent': none_percent,
            }
            periods.append(period)
        stats.append({
            'party': party,
            'periods': periods,
        })
    logger.info('END')
    return stats
