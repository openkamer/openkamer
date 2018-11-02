import logging

from django.core.management.base import BaseCommand

import openkamer.parliament

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        openkamer.parliament.create_parliament_and_government()
