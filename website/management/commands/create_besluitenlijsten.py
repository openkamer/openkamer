import traceback
import logging

from django.core.management.base import BaseCommand

import scraper.besluitenlijst

from website.create import create_besluitenlijst

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        commissies = scraper.besluitenlijst.get_voortouwcommissies_besluiten_urls()
        for commissie in commissies:
            urls = scraper.besluitenlijst.get_besluitenlijsten_urls(commissie['url'])
            for url in urls:
                create_besluitenlijst(url)
