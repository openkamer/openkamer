import logging

from django.core.management.base import BaseCommand

import website.create

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
        website.create.create_parties()
        website.create.create_governments()
        website.create.create_parliament_members()
        failed_dossiers = website.create.create_wetsvoorstellen_all(options['skip-existing'])
        if failed_dossiers:
            logger.error('the following dossiers failed: ' + str(failed_dossiers))
        website.create.create_besluitenlijsten(skip_existing=options['skip-existing'])
