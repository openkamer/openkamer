import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from document.models import Document
from document.models import Submitter

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.do()

    @transaction.atomic
    def do(self):
        submitters = Submitter.objects.all()
        documents = Document.objects.all()
        counter = 1
        n_docs = documents.count()
        print(n_docs)
        for document in documents:
            print('document ' +  str(counter) + '/' + str(n_docs))
            doc_submitters = submitters.filter(document=document)
            person_ids = []
            for doc_sub in doc_submitters:
                if doc_sub.person.id in person_ids:
                    doc_sub.delete()
                else:
                    person_ids.append(doc_sub.person.id)
            counter += 1
