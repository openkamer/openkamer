from django.core.management.base import BaseCommand

from document.models import VoteParty
from document.models import VoteIndividual

from django.db import transaction


class Command(BaseCommand):
    """
    Sets the raw party and person name in vote models based on their foreign keys.
    This is only used when updating a database in which these fields are not set.
    Normally, the foreign keys will be derived from the raw party/person name.
    TODO: remove this after upgrade
    """

    def handle(self, *args, **options):
        self.update()

    @transaction.atomic
    def update(self):
        votes = VoteIndividual.objects.all()
        for vote in votes:
            if not vote.parliament_member:
                continue
            person = vote.parliament_member.person
            vote.person_name = person.surname + ', ' + person.initials
            vote.save()
        votes = VoteParty.objects.all()
        for vote in votes:
            vote.party_name = vote.party.name_short
            vote.save()
