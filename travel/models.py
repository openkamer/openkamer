import logging

from django.db import models

from person.models import Person
from parliament.models import ParliamentMember
from parliament.models import PoliticalParty, PartyMember

logger = logging.getLogger(__name__)


class TravelPersonPosition(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    party = models.ForeignKey(PoliticalParty, null=True, blank=True, on_delete=models.CASCADE)
    parliament_member = models.ForeignKey(ParliamentMember, null=True, blank=True, on_delete=models.CASCADE)
    date = models.DateField()

    class Meta:
        unique_together = ['person', 'date']

    def save(self, *args, **kwargs):
        party_members = PartyMember.get_at_date(self.person, self.date)
        self.party = party_members[0].party if party_members else None
        parliament_members = ParliamentMember.find_at_date(self.person, self.date)
        self.parliament_member = parliament_members[0] if parliament_members else None
        super().save(*args, **kwargs)


class Travel(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    person_position = models.ForeignKey(TravelPersonPosition, on_delete=models.CASCADE)
    destination = models.CharField(max_length=1000, default='', blank=True)
    purpose = models.CharField(max_length=1000, default='', blank=True)
    paid_by = models.CharField(max_length=1000, default='', blank=True)
    date_begin = models.DateField()
    date_end = models.DateField()

    def save(self, *args, **kwargs):
        self.person_position, created = TravelPersonPosition.objects.get_or_create(
            person=self.person,
            date=self.date_begin
        )
        super().save(*args, **kwargs)
