from django.core.management.base import BaseCommand

from document.models import Dossier


class Command(BaseCommand):

    def handle(self, *args, **options):
        dossiers = Dossier.objects.all()
        for dossier in dossiers:
            dossier.set_derived_fields()


