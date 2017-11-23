from django.core.management.base import BaseCommand

from openkamer.verslagao import create_verslagen_algemeen_overleg


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('year', nargs='+', type=int)
        parser.add_argument('--max', type=int, help='The max number of documents to create, used for testing.', default=None)

    def handle(self, *args, **options):
        year = options['year'][0]
        max_n = options['max']
        create_verslagen_algemeen_overleg(year, max_n, skip_if_exists=False)
