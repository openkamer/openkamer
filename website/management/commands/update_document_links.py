from django.core.management.base import BaseCommand

from document.models import Document
import website.create


class Command(BaseCommand):

    def handle(self, *args, **options):
        documents = Document.objects.all()
        counter = 0
        for document in documents:
            if not document.content_html:
                continue
            document.content_html = website.create.update_document_html_links(document.content_html)
            document.save()
            counter += 1
            print(counter)
