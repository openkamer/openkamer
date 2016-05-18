from django.core.management.base import BaseCommand

from document.models import Document, Kamerstuk, Dossier
import scraper.documents


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('dossier_id', nargs='+', type=int)

    def handle(self, *args, **options):
        # dossier_id = 33885
        dossier_id = options['dossier_id'][0]
        print('delete documents with dossier: ' + str(dossier_id))
        dossier_docs = Document.objects.filter(dossier=Dossier.objects.get(dossier_id=dossier_id))
        for doc in dossier_docs:
            print('delete document')
            doc.delete()
