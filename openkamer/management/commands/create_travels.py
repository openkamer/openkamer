from django.core.management.base import BaseCommand

from openkamer.travel import create_travels


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--max', type=int, help='The max number of travels to create, for testing.', default=None)

    def handle(self, *args, **options):
        max_items = options['max']
        create_travels(max_items=max_items)
