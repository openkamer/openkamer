
import logging
logger = logging.getLogger(__name__)

from django.db import models


class Party(models.Model):
    name = models.CharField(max_length=200)
    seats = models.IntegerField()
    url = models.URLField(blank=True, null=False, default='')

    def __str__(self):
        return self.name


class Member(models.Model):
    name = models.CharField(max_length=200)
    party = models.ForeignKey(Party)

    def __str__(self):
        return self.name + ' (' + str(self.party) + ')'


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
    author = models.ForeignKey(Member)
    type = models.CharField(max_length=2, choices=TYPES)
    date = models.DateField(auto_now=True)
    document_url = models.URLField(blank=True, null=False, default='')

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
    party = models.ForeignKey(Party)
    decision = models.CharField(max_length=2, choices=CHOICES)
    details = models.CharField(max_length=2000, blank=True, null=False, default='')

    def __str__(self):
        return str(self.bill) + ' - ' + str(self.party) + ' - ' + self.decision