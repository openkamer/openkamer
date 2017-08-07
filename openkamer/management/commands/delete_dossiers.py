import logging

from django.core.management.base import BaseCommand

from document.models import Dossier

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        Dossier.objects.all().delete()