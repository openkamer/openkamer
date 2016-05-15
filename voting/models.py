from datetime import datetime

from django.db import models

from parliament.models import PoliticalParty, PartyMember


class Bill(models.Model):
    AMENDEMENT = 'AM'
    MOTIE = 'MO'
    WETSVOORSTEL = 'WV'

    TYPES = (
        (AMENDEMENT, 'Amendement'),
        (MOTIE, 'Motie'),
        (WETSVOORSTEL, 'Wetsvoorstel'),
    )

    title = models.CharField(max_length=500)
    original_title = models.CharField(max_length=500, blank=True, null=False, default='')
    author = models.ForeignKey(PartyMember)
    type = models.CharField(max_length=2, choices=TYPES)
    datetime = models.DateTimeField(default=datetime.now, editable=True, blank=True)
    document_url = models.URLField(blank=True, null=False, default='')

    def get_votes(self):
        return Vote.objects.filter(bill=self)

    def __str__(self):
        return self.title + ' (' + str(self.author) + ')'


class Vote(models.Model):
    FOR = 'FO'
    AGAINST = 'AG'

    CHOICES = (
        (FOR, 'Voor'),
        (AGAINST, 'Tegen'),
    )

    bill = models.ForeignKey(Bill)
    party = models.ForeignKey(PoliticalParty)
    number_of_seats = models.IntegerField()
    decision = models.CharField(max_length=2, choices=CHOICES)
    details = models.CharField(max_length=2000, blank=True, null=False, default='')

    def __str__(self):
        return str(self.bill) + ' - ' + str(self.party) + ' - ' + self.decision 
