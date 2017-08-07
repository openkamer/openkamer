import traceback
import logging


from django.core.management.base import BaseCommand

from openkamer.besluitenlijst import create_besluitenlijsten

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            dest='skip-existing',
            default=False,
            help='Do not create besluitenlijsten that already exist.',
        )

    def handle(self, *args, **options):
        try:
            create_besluitenlijsten(skip_existing=options['skip-existing'])
        except:
            logger.error('while trying to create besluitenlijsten')
            logger.error(traceback.format_exc())
            raise
