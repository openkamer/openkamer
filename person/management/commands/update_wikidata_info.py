from django.core.management.base import BaseCommand

from person.models import Person


class Command(BaseCommand):

    def handle(self, *args, **options):
        persons = Person.objects.all()
        for person in persons:
            person.set_wikidata_info()
            person.save()
