import logging

from django.core.management.base import BaseCommand

from parliament.models import Parliament
from openkamer.parliament import add_tk_person_id

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        for member in Parliament.get_or_create_tweede_kamer().members:
            person = add_tk_person_id(member.person)
            if not person.tk_id:
                print('NOT FOUND FOR : {} ({})'.format(person.surname, person.initials))
