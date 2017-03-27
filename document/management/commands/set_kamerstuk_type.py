from django.core.management.base import BaseCommand

from document.models import Kamerstuk

from django.db import transaction


class Command(BaseCommand):

    @transaction.atomic
    def handle(self, *args, **options):
        kamerstukken = Kamerstuk.objects.all()
        for kamerstuk in kamerstukken:
            kamerstuk.save()
