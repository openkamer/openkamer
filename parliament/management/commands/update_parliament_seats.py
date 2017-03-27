from django.core.management.base import BaseCommand

from parliament.models import PoliticalParty


class Command(BaseCommand):

    def handle(self, *args, **options):
        for party in PoliticalParty.objects.all():
            party.set_current_parliament_seats()
