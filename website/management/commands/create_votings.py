from django.core.management.base import BaseCommand

from website.create import create_votings


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('dossier_id', nargs='+', type=int)

    def handle(self, *args, **options):
        # dossier_id = 33885
        create_votings(options['dossier_id'][0])




