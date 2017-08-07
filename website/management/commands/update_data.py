from django.core.management.base import BaseCommand

from person.models import Person
from parliament.models import PoliticalParty

import openkamer.parliament


class Command(BaseCommand):

    def handle(self, *args, **options):
        Person.update_persons_all('nl')
        openkamer.parliament.update_initials()

        parties = PoliticalParty.objects.all()
        for party in parties:
            party.update_info(language='nl')
