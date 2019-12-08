import logging

from django.core.management.base import BaseCommand

from parliament.models import PoliticalParty
from openkamer.parliament import create_party_members

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        create_party_members()
