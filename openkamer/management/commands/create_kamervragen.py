from django.core.management.base import BaseCommand

from openkamer.kamervraag import create_kamervraag

from document.models import Kamervraag


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('year', nargs='+', type=int)
        parser.add_argument('--max', type=int, help='The max number of documents to create, used for testing.', default=1e99)

    def handle(self, *args, **options):
        Kamervraag.objects.all().delete()
        year = options['year'][0]
        max_n = options['max']
        infos = Kamervraag.get_kamervragen_info(year)
        counter = 0
        for info in infos:
            create_kamervraag(info)
            if counter >= max_n:
                return
            counter += 1

