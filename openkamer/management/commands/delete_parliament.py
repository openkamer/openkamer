import logging

from django.core.management.base import BaseCommand

from parliament.models import ParliamentMember, Parliament

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        Parliament.objects.all().delete()
        ParliamentMember.objects.all().delete()