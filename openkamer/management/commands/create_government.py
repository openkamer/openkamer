from django.core.management.base import BaseCommand

from openkamer.parliament import create_government


class Command(BaseCommand):
    # Balkenende III : Q1473297
    # Balkenende IV : Q1719725
    # Rutte I : Q168828
    # Rutte II : Q1638648
    # Rutte III : Q42293409
    # Rutte IV : Q110111120
    # Schoof: Q126527270

    def add_arguments(self, parser):
        parser.add_argument('wikidata_id', nargs='+', type=str)

    def handle(self, *args, **options):
        wikidata_id = options['wikidata_id'][0]
        create_government(wikidata_id)
