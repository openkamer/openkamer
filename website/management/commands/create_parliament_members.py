from django.core.management.base import BaseCommand

from scraper import parliament_members


class Command(BaseCommand):

    def handle(self, *args, **options):
        parliament_members.create_members()
