from django.core.management.base import BaseCommand

import scraper.political_parties
import scraper.parliament_members
import scraper.government

from person.models import Person
import website.create


class Command(BaseCommand):
    MAX_TRIES = 3

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            dest='skip-existing',
            default=False,
            help='Do not create items that already exist.',
        )

    def handle(self, *args, **options):
        website.create.create_parties()
        website.create.create_governments()
        website.create.create_parliament_members_from_wikidata()
        website.create.create_wetsvoorstellen_all(options['skip-existing'])
        website.create.create_besluitenlijsten(skip_existing=options['skip-existing'])
