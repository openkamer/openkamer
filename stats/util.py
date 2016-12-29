import logging

from document.models import Vote
from document.models import VoteParty

from government.models import Government
from parliament.models import PoliticalParty


logger = logging.getLogger(__name__)


def get_party_votes_for_government(government):
    logger.info('BEGIN')
    votes_party = VoteParty.objects.filter(voting__date__gte=government.date_formed)
    if government.date_dissolved:
        votes_party = votes_party.filter(voting__date__lt=government.date_dissolved)
    logger.info('END')
    return votes_party
