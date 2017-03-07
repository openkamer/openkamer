from django.core.management.base import BaseCommand

from openkamer.kamervraag import create_kamerantwoord, create_antwoorden

from document.models import Kamerantwoord


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('year', nargs='+', type=int)
        parser.add_argument('--max', type=int, help='The max number of documents to create, used for testing.', default=None)

    def handle(self, *args, **options):
        year = options['year'][0]
        max_n = options['max']
        create_antwoorden(year, max_n)

