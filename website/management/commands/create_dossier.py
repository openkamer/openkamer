from django.core.management.base import BaseCommand

from document.models import create_or_update_dossier


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('dossier_id', nargs='+', type=int)

    def handle(self, *args, **options):
        # dossier_id = 33885
        dossier_id = options['dossier_id'][0]
        create_or_update_dossier(str(dossier_id))


