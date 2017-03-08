from django.core.management.base import BaseCommand

from openkamer.kamervraag import create_kamerantwoord, create_antwoorden

from document.models import Kamervraag


class Command(BaseCommand):

    def handle(self, *args, **options):
        Kamervraag.objects.all().delete()
