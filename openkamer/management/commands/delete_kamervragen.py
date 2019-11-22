from django.core.management.base import BaseCommand

from document.models import Kamervraag


class Command(BaseCommand):

    def handle(self, *args, **options):
        Kamervraag.objects.all().delete()
