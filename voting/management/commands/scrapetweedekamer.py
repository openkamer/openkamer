import urllib.request
from datetime import datetime

import lxml.html

from django.core.management.base import BaseCommand

from scraper import votings


class Command(BaseCommand):

    def handle(self, *args, **options):
        votings.create_members()
        # votings.get_bills()
