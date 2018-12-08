from django.core.management.base import BaseCommand

from openkamer.gift import create_gifts


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--max', type=int, help='The max number of gifts to create, for testing.', default=None)

    def handle(self, *args, **options):
        max_items = options['max']
        create_gifts(max_items=max_items)
