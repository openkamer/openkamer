from django.core.management.base import BaseCommand

from person.models import Person


class Command(BaseCommand):

    def handle(self, *args, **options):
        Person.update_persons_all(language='nl')
