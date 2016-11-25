import traceback
import logging

from django.core.management.base import BaseCommand

import website.create

logger = logging.getLogger(__name__)


class Command(BaseCommand):

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
        website.create.create_wetsvoorstellen(options['skip-existing'])
