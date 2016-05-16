from django.core.management.base import BaseCommand

import scraper.parliament_members


class Command(BaseCommand):

    def handle(self, *args, **options):
        scraper.parliament_members.create_members()
