
import logging
logger = logging.getLogger(__name__)

from datetime import datetime

from django.db import models


class Party(models.Model):
    name = models.CharField(max_length=200)
    seats = models.IntegerField()
    url = models.URLField(blank=True, null=False, default='')
    icon_url = models.ImageField(blank=True, null=True)

    def __str__(self):
        return self.name


class Member(models.Model):
    MALE = 'M'
    FEMALE = 'F'

    SEX = (
        (MALE, 'Man'),
        (FEMALE, 'Vrouw'),
    )

    forename = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    surname_prefix = models.CharField(max_length=200, blank=True, null=True, default='')
    age = models.IntegerField()
    sex = models.CharField(max_length=1, choices=SEX)
    residence = models.CharField(max_length=200, blank=True, null=True, default='')
    party = models.ForeignKey(Party)

    def get_full_name(self):
        fullname = self.forename
        if self.surname_prefix:
            fullname += ' ' + self. surname_prefix
        fullname += ' ' + self.surname
        return fullname

    def __str__(self):
        return self.get_full_name() + ' (' + str(self.party) + ')'


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
    party = models.ForeignKey(Party)
    decision = models.CharField(max_length=2, choices=CHOICES)
    details = models.CharField(max_length=2000, blank=True, null=False, default='')

    def __str__(self):
        return str(self.bill) + ' - ' + str(self.party) + ' - ' + self.decision 
