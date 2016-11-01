import traceback
import logging


from django.core.management.base import BaseCommand

from website.create import create_besluitenlijsten

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        create_besluitenlijsten()
