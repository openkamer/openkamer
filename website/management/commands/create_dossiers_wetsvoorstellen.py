import traceback
import logging

from django.core.management.base import BaseCommand

from document.models import Dossier

from website.create import create_or_update_dossier, create_dossier_retry_on_error

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    MAX_TRIES = 3

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            dest='skip-existing',
            default=False,
            help='Do not create dossiers that already exist.',
        )

    def handle(self, *args, **options):
        self.create_dossiers_from_file('data/dossier_ids_wetsvoorstellen_initiatief.txt', options['skip-existing'])
        self.create_dossiers_from_file('data/dossier_ids_wetsvoorstellen_regering.txt', options['skip-existing'])

    @staticmethod
    def create_dossiers_from_file(filename, skip_existing=False):
        with open(filename, 'r') as filein:
            lines = filein.read().splitlines()
        failed_dossiers = []
        for line in lines:
            dossier_id = line.strip()
            dossiers = Dossier.objects.filter(dossier_id=dossier_id)
            if skip_existing and dossiers.exists():
                logger.info('dossier already exists, skip')
                continue
            try:
                create_dossier_retry_on_error(dossier_id=dossier_id, max_tries=Command.MAX_TRIES)
            except Exception as e:
                failed_dossiers.append(dossier_id)
                logger.error('error for dossier id: ' + str(dossier_id))
                logger.error(traceback.format_exc())
        logger.error('failed dossiers: ' + str(failed_dossiers))