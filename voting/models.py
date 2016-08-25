from django.db import models

from parliament.models import PoliticalParty

from document.models import Kamerstuk, Dossier


class Voting(models.Model):
    AANGENOMEN = 'AAN'
    VERWORPEN = 'VER'
    INGETROKKEN = 'ING'
    AANGEHOUDEN = 'AGH'
    CHOICES = (
        (AANGENOMEN, 'Aangenomen'), (VERWORPEN, 'Verworpen'), (INGETROKKEN, 'Ingetrokken'), (AANGEHOUDEN, 'Aangehouden')
    )
    dossier = models.ForeignKey(Dossier)
    kamerstuk = models.ForeignKey(Kamerstuk, blank=True, null=True)
    result = models.CharField(max_length=3, choices=CHOICES)
    date = models.DateField(auto_now=False, blank=True)


class Vote(models.Model):
    FOR = 'FO'
    AGAINST = 'AG'
    CHOICES = (
        (FOR, 'Voor'), (AGAINST, 'Tegen'),
    )

    voting = models.ForeignKey(Voting)
    party = models.ForeignKey(PoliticalParty)
    number_of_seats = models.IntegerField()
    decision = models.CharField(max_length=2, choices=CHOICES)
    details = models.CharField(max_length=2000, blank=True, null=False, default='')

    def __str__(self):
        return str(self.voting) + ' - ' + str(self.party) + ' - ' + str(self.decision)
