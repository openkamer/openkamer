import logging

from django.core.management.base import BaseCommand

from document.models import Kamerstuk

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        Kamerstuk.objects.filter(type=Kamerstuk.VERSLAG_AO).delete()
