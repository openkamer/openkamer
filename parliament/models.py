from django.db import models

from person.models import Person


class Parliament(models.Model):
    name = models.CharField(max_length=200)
    wikidata_uri = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return str(self.name)


class ParliamentMember(models.Model):
    person = models.ForeignKey(Person)
    parliament = models.ForeignKey(Parliament)
    joined = models.DateField(blank=True, null=True)
    left = models.DateField(blank=True, null=True)

    def __str__(self):
        return str(self.person) + ' (' + str(self.parliament) + ')'


class PoliticalParty(models.Model):
    name = models.CharField(max_length=200)
    founded = models.DateField(blank=True, null=True)
    dissolved = models.DateField(blank=True, null=True)
    logo = models.ImageField(blank=True)
    wikidata_uri = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return str(self.name)

    @staticmethod
    def get_or_create_party(party_name):
        party = PoliticalParty.objects.filter(name=party_name)
        if party.exists():
            return party[0]
        party = PoliticalParty.objects.create(name=party_name)
        party.save()
        return party

    class Meta:
        verbose_name_plural = "Political parties"


class PartyMember(models.Model):
    person = models.ForeignKey(Person)
    party = models.ForeignKey(PoliticalParty)
    joined = models.DateField(blank=True, null=True)
    left = models.DateField(blank=True, null=True)

    def __str__(self):
        return str(self.person) + ' (' + str(self.party) + ')'
