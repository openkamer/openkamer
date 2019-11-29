from django.core.management.base import BaseCommand

from document.models import Dossier


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('dossier_id', nargs='+', type=str)

    def handle(self, *args, **options):
        # dossier_id = 33885
        dossier_id = options['dossier_id'][0]
        Dossier.objects.filter(dossier_id=dossier_id).delete()
