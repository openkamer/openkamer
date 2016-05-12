from django.db import models


class Person(models.Model):
    forename = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    surname_prefix = models.CharField(max_length=200, blank=True, null=True, default='')
    residence = models.CharField(max_length=200, blank=True, null=True, default='')
    wikidata_url = models.URLField(max_length=200, blank=True)


class Parliament(models.Model):
    name = models.CharField(max_length=200)
    wikidata_url = models.URLField(max_length=200, blank=True)


class ParliamentMember(models.Model):
    person = models.ForeignKey(Person)
    parliament = models.ForeignKey(Parliament)
    joined = models.DateField(blank=False)
    left = models.DateField(blank=True)


class PoliticalParty(models.Model):
    name = models.CharField(max_length=200)
    founded = models.DateField(blank=False)
    dissolved = models.DateField(blank=True)
    wikidata_url = models.URLField(max_length=200, blank=True)

    class Meta:
        verbose_name_plural = "Political parties"


class PartyMember(models.Model):
    person = models.ForeignKey(Person)
    party = models.ForeignKey(PoliticalParty)
