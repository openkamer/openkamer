import logging

from django.core.management.base import BaseCommand

import stats.models

import openkamer.besluitenlijst
import openkamer.dossier
import openkamer.parliament
import openkamer.kamervraag

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
            help='Do not create items that already exist.',
        )

    def handle(self, *args, **options):
        openkamer.parliament.create_parliament_and_government()
        failed_dossiers = openkamer.dossier.create_wetsvoorstellen_all(options['skip-existing'])
        if failed_dossiers:
            logger.error('the following dossiers failed: ' + str(failed_dossiers))
        openkamer.kamervraag.create_kamervragen(year=2019)
        stats.models.update_all()
