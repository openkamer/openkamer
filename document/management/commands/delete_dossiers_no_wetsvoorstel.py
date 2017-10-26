from django.core.management.base import BaseCommand

from document.models import Dossier

from django.db import transaction


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.do()

    @transaction.atomic
    def do(self):
        wetsvoorstel_ids = Dossier.get_dossier_ids()
        Dossier.objects.exclude(dossier_id__in=wetsvoorstel_ids).delete()
