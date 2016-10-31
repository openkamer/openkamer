import traceback
import logging

from django.core.management.base import BaseCommand

from website.create import create_besluitenlijst

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('url', nargs='+', type=str)

    def handle(self, *args, **options):
        url = options['url'][0]
        create_besluitenlijst(url)