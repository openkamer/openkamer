import traceback
import logging


from django.core.management.base import BaseCommand

from website.create import create_besluitenlijsten

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        try:
            create_besluitenlijsten()
        except:
            logger.error('while trying to create besluitenlijsten')
            logger.error(traceback.format_exc())
            raise
