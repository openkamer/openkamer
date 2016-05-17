from django.core.management.base import BaseCommand

from person.models import Person
from parliament.models import PoliticalParty


class Command(BaseCommand):

    def handle(self, *args, **options):
        persons = Person.objects.all()
        for person in persons:
            person.update_info('nl')
            person.save()

        parties = PoliticalParty.objects.all()
        for party in parties:
            party.update_info(language='nl', top_level_domain='nl')
