from django.core.management.base import BaseCommand

from document.models import Document, Kamerstuk
import scraper.documents


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('dossier_id', nargs='+', type=int)

    def handle(self, *args, **options):
        # dossier_id = 33885
        dossier_id = options['dossier_id'][0]
        search_results = scraper.documents.search_politieknl_dossier(dossier_id)
        for result in search_results:
            document = Document.objects.create(
                dossier_id=str(dossier_id),
                raw_type=result['type'],
                raw_title=result['title'],
                publisher=result['publisher'],
                date_published=result['published_date'],
                document_url=result['page_url'],
            )

            if 'Kamerstuk' in result['type']:
                print('KAMERSTUK')
                print(result['type'])
                items = result['type'].split(' ')
                print(items)
                title_parts = result['title'].split(';')
                type_short = ''
                type_long = ''
                if len(title_parts) > 2:
                    type_short = title_parts[1].strip()
                    type_long = title_parts[2].strip()
                if "Bijlage" in result['type']:
                    print('BIJLAGE')
                    id_main = int(items[4])
                    id_sub = int(items[6])
                else:
                    id_main = int(items[2])
                    id_sub = int(items[4])
                Kamerstuk.objects.create(
                    document=document,
                    id_main=id_main,
                    id_sub=id_sub,
                    type_short=type_short,
                    type_long=type_long,
                )
