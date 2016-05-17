from django.core.management.base import BaseCommand

from parliament.models import PoliticalParty


class Command(BaseCommand):

    def handle(self, *args, **options):
        parties = PoliticalParty.objects.all()
        for party in parties:
            party.update_info(language='nl', top_level_domain='nl')
