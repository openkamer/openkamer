from django.core.management.base import BaseCommand

import stats.models


class Command(BaseCommand):

    def handle(self, *args, **options):
        stats.models.Plot.create()
