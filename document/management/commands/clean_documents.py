import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db import models

from document.models import Agenda
from document.models import Document
from document.models import Kamerstuk
from document.models import Kamervraag
from document.models import Kamerantwoord

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Remove duplicate documents and documents without relations"""

    def handle(self, *args, **options):
        self.do()

    @transaction.atomic
    def do(self):
        unique_together_fields = ['document_id']
        Command.remove_duplicates(unique_together_fields)
        Command.remove_unrelated()
        # unique_together_fields = ['source_url']
        # Command.remove_duplicates(unique_together_fields)
        # unique_together_fields = ['title_short']
        # Command.remove_duplicates(unique_together_fields)
        # relations = Command.find_relations()
        # for relation in relations:
        #     print(relation)

    @staticmethod
    def remove_unrelated():
        deleted_ids = []
        for document in Document.objects.only('id'):
            if Kamerstuk.objects.filter(document__id=document.id):
                continue
            if Kamervraag.objects.filter(document__id=document.id):
                continue
            if Kamerantwoord.objects.filter(document__id=document.id):
                continue
            if Agenda.objects.filter(document__id=document.id):
                continue
            deleted_ids.append(document.id)
            document.delete()
        print('no relation: ' + str(len(deleted_ids)))

    @staticmethod
    def remove_duplicates(unique_together_fields):
        duplicates = (Document.objects.values(*unique_together_fields)
                      .order_by()
                      .annotate(max_id=models.Max('id'),
                                count_id=models.Count('id'))
                      .filter(count_id__gt=1))

        print('duplicates: ' + str(len(duplicates)))

        for duplicate in duplicates:
            (Document.objects.filter(**{x: duplicate[x] for x in unique_together_fields})
             .exclude(id=duplicate['max_id'])
             .delete())

    @staticmethod
    def find_relations():
        return [
            f for f in Document._meta.get_fields()
            if f.auto_created and not f.concrete
        ]
