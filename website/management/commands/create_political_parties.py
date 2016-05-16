from django.core.management.base import BaseCommand

import scraper.politcal_parties


class Command(BaseCommand):

    def handle(self, *args, **options):
        scraper.politcal_parties.create_parties()
