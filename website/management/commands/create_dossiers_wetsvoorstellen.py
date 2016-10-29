import traceback
import logging

from django.core.management.base import BaseCommand

from website.create import create_or_update_dossier, create_dossier_retry_on_error

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    MAX_TRIES = 3

    def handle(self, *args, **options):
        self.create_dossiers_from_file('data/dossier_ids_wetsvoorstellen_initiatief.txt')
        self.create_dossiers_from_file('data/dossier_ids_wetsvoorstellen_regering.txt')

    @staticmethod
    def create_dossiers_from_file(filename):
        with open(filename, 'r') as filein:
            lines = filein.read().splitlines()
            for line in lines:
                try:
                    create_dossier_retry_on_error(dossier_id=line.strip(), max_tries=MAX_TRIES)
                except Exception as e:
                    logger.error(traceback.format_exc())
