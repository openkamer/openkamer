import urllib.request
from datetime import datetime

import lxml.html

from django.core.management.base import BaseCommand

from voting.models import Party
from voting.models import Member
from voting.models import Bill
from voting.models import Vote

from scraper import votings


class Command(BaseCommand):

    def handle(self, *args, **options):
        votings.scrape()
