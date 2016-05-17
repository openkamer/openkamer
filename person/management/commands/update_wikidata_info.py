from django.core.management.base import BaseCommand

from person.models import Person


class Command(BaseCommand):

    def handle(self, *args, **options):
        persons = Person.objects.all()
        for person in persons:
            person.update_info('nl')
            person.save()
