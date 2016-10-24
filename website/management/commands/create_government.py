from django.core.management.base import BaseCommand

from website.create import create_government


class Command(BaseCommand):
    # Rutte I : Q168828
    # Rutte II : Q1638648

    def add_arguments(self, parser):
        parser.add_argument('wikidata_id', nargs='+', type=str)

    def handle(self, *args, **options):
        wikidata_id = options['wikidata_id'][0]
        create_government(wikidata_id)
