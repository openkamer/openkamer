from django.core.management.base import BaseCommand

from document.models import Voting
from document.models import VoteParty
from document.models import VoteIndividual

from django.db import transaction


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.update()

    @transaction.atomic
    def update(self):
        votings = Voting.objects.all()
        for voting in votings:
            voting.is_individual = voting.votes_individual.exists()
            voting.save()
