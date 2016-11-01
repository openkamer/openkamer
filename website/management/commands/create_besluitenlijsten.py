import traceback
import logging

from pdfminer.pdfparser import PDFSyntaxError

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
                try:
                    create_besluitenlijst(url)
                except PDFSyntaxError as e:
                    logger.error('failed to donwload and parse besluitenlijst with url: ' + url)