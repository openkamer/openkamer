
import logging
logger = logging.getLogger(__name__)

from django.db import models


class Party(models.Model):
    name = models.CharField(max_length=200)
    seats = models.IntegerField()
    url = models.URLField()


class Member(models.Model):
    title = models.CharField(max_length=200)
    party = models.ForeignKey(Party)


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
    original_title = models.CharField(max_length=500)
    author = models.ForeignKey(Member)
    type = models.CharField(max_length=2, choices=TYPES)
    date = models.DateField(auto_now=True)
    document_url = models.URLField()


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
    details = models.CharField(max_length=2000)