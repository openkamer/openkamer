from django.core.management.base import BaseCommand

from openkamer.kamervraag import link_kamervragen_and_antwoorden


class Command(BaseCommand):

    def handle(self, *args, **options):
        link_kamervragen_and_antwoorden()
