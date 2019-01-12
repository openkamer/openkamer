import datetime

from django.core.management.base import BaseCommand

import stats.models


class Command(BaseCommand):

    def handle(self, *args, **options):
        start_date = datetime.date(year=2010, month=1, day=1)
        stats.models.SeatsPerParty.create_all(start_date)
