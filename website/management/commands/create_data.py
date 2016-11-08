from django.core.management.base import BaseCommand

import scraper.political_parties
import scraper.parliament_members
import scraper.government

from person.models import Person
import website.create


class Command(BaseCommand):

    def handle(self, *args, **options):
        website.create.create_parties()
        website.create.create_governments()
        website.create.create_parliamemt_members()
        Person.update_persons_all('nl')

        # add a few demo dossiers
        website.create.create_or_update_dossier('33885')
        website.create.create_or_update_dossier('34344')
        website.create.create_or_update_dossier('33506')

        website.create.create_besluitenlijsten(max_results_per_commission=20)

