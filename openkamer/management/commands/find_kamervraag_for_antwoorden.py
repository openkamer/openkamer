from django.core.management.base import BaseCommand

from openkamer.kamervraag import find_kamerantwoorden


class Command(BaseCommand):

    def handle(self, *args, **options):
        find_kamerantwoorden()
