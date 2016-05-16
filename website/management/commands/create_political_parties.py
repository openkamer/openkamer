from django.core.management.base import BaseCommand

import scraper.political_parties


class Command(BaseCommand):

    def handle(self, *args, **options):
        scraper.political_parties.create_parties()
