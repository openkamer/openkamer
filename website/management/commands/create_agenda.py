from django.core.management.base import BaseCommand

from openkamer.agenda import create_or_update_agenda


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('agenda_data', nargs='+', type=str)
        #specify date as string

    def handle(self, *args, **options):
        #agenda_date = '2015-09-18'

        agenda_date = options['agenda_data'][0]
        if len(agenda_date) == 10 and agenda_date[4] == '-' and agenda_date[7] == '-' :
            print("Creating/updating agenda of", agenda_date)
        else:
            raise NameError("please format date as yyyy-mm-dd")
            
        create_or_update_agenda("ag-tk-"+agenda_date)
