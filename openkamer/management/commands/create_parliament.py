from django.core.management.base import BaseCommand

import openkamer.parliament


class Command(BaseCommand):

    def handle(self, *args, **options):
        openkamer.parliament.create_parliament_members()
