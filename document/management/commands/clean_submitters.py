import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db import models

from document.models import Submitter

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Remove duplicate submitters"""

    def handle(self, *args, **options):
        self.do()

    @transaction.atomic
    def do(self):
        unique_fields = ['person', 'document']

        duplicates = (Submitter.objects.values(*unique_fields)
                      .order_by()
                      .annotate(max_id=models.Max('id'),
                                count_id=models.Count('id'))
                      .filter(count_id__gt=1))

        for duplicate in duplicates:
            (Submitter.objects.filter(**{x: duplicate[x] for x in unique_fields})
             .exclude(id=duplicate['max_id'])
             .delete())
