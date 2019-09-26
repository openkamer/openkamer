import logging

from django.db import models

from person.models import Person
from parliament.models import ParliamentMember
from parliament.models import PoliticalParty, PartyMember

logger = logging.getLogger(__name__)


class PersonPosition(models.Model):
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


class Gift(models.Model):
    BOEK = 'BOEK'
    TOEGANGSKAART = 'KAAR'
    WIJN = 'WIJN'
    DINER = 'DINE'
    BLOEMEN = 'BLOE'
    PAKKET = 'PAKK'
    KLEDING = 'KLED'
    ONBEKEND = 'ONB'
    TYPE_CHOICES = (
        (BOEK, 'Boek'), (TOEGANGSKAART, 'Toegangskaart'), (WIJN, 'Wijn'),
        (BLOEMEN, 'Bloemen'), (PAKKET, 'Pakket'), (KLEDING, 'Kleding'), (DINER, 'Diner'),
        (ONBEKEND, 'Onbekend')
    )
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    person_position = models.ForeignKey(PersonPosition, on_delete=models.CASCADE)
    description = models.CharField(max_length=1000, default='', blank=True)
    date = models.DateField(null=True, blank=True)
    value_euro = models.FloatField(null=True, blank=True)
    type = models.CharField(max_length=4, choices=TYPE_CHOICES, default=ONBEKEND, db_index=True)

    def save(self, *args, **kwargs):
        self.person_position, created = PersonPosition.objects.get_or_create(
            person=self.person,
            date=self.date
        )
        super().save(*args, **kwargs)

    @staticmethod
    def calc_sum_average(gifts):
        gifts = gifts.filter(value_euro__isnull=False)
        gifts_value = 0
        for gift in gifts:
            gifts_value += gift.value_euro
        average = 0
        if gifts.count() != 0:
            average = gifts_value / gifts.count()
        return gifts_value, average
