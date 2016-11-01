import traceback
import logging

from pdfminer.pdfparser import PDFSyntaxError

from django.core.management.base import BaseCommand

from document.models import BesluitenLijst

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        BesluitenLijst.objects.all().delete()