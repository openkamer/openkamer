from django.core.management.base import BaseCommand

import scraper.political_parties
import scraper.parliament_members

from person.models import Person
from website.create import create_or_update_dossier


class Command(BaseCommand):

    def handle(self, *args, **options):
        scraper.political_parties.create_parties()
        scraper.parliament_members.create_members()
        Person.update_persons_all('nl')

        # add a few demo dossiers
        create_or_update_dossier('33885')
        create_or_update_dossier('34344')