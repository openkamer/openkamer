import logging

from django.core.management.base import BaseCommand

from person.models import Person
from openkamer.parliament import add_tk_person_id

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        for person in Person.objects.all():
            person = add_tk_person_id(person)
            if not person.tk_id:
                print('NOT FOUND FOR : {} ({})'.format(person.surname, person.initials))
