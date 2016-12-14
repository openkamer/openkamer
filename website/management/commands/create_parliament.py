from django.core.management.base import BaseCommand

import website.create


class Command(BaseCommand):

    def handle(self, *args, **options):
        website.create.create_parliament_members_from_tweedekamer_data()
