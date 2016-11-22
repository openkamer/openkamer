from django.core.management.base import BaseCommand

from document.models import Dossier
from document.models import CategoryDossier


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('dossier_id', nargs='+', type=int)

    def handle(self, *args, **options):
        # dossier_id = 33885
        dossier_id = options['dossier_id'][0]
        Dossier.objects.filter(dossier_id=dossier_id).delete()
