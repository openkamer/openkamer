import logging

from django.core.management.base import BaseCommand

from parliament.models import PoliticalParty
from openkamer.parliament import create_parties

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        parties = create_parties(update_votes=False, active_only=False)
        for party in parties:
            print('party created:', party.name, party.name_short, party.wikidata_id)
