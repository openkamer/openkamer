from django.core.management.base import BaseCommand

from openkamer.parliament import create_governments


class Command(BaseCommand):

    def handle(self, *args, **options):
        create_governments()
