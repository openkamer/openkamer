from django.core.management.base import BaseCommand

from document.models import Dossier
from document.create import get_dossier_ids

from django.db import transaction


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.do()

    @transaction.atomic
    def do(self):
        dossiers = get_dossier_ids()
        dossier_main_ids = [Dossier.create_dossier_id(dossier.dossier_id, dossier.dossier_sub_id) for dossier in dossiers]
        Dossier.objects.exclude(dossier_id__in=dossier_main_ids).delete()
