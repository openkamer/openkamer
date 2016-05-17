from django.core.management.base import BaseCommand

import scraper


class Command(BaseCommand):

    def handle(self, *args, **options):
        scraper.political_parties.create_parties()
        scraper.parliament_members.create_members()
