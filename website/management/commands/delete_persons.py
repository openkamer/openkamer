import logging

from django.core.management.base import BaseCommand

from person.models import Person

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        Person.objects.all().delete()
