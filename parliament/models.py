from django.db import models


class Person(models.Model):
    forename = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    surname_prefix = models.CharField(max_length=200, blank=True, null=True, default='')
    wikidata_uri = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        fullname = self.forename
        if self.surname_prefix:
            fullname += ' ' + str(self.surname_prefix)
        fullname += ' ' + str(self.surname)
        return fullname


class Parliament(models.Model):
    name = models.CharField(max_length=200)
    wikidata_uri = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return str(self.name)


class ParliamentMember(models.Model):
    person = models.ForeignKey(Person)
    parliament = models.ForeignKey(Parliament)
    joined = models.DateField(blank=False)
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

    class Meta:
        verbose_name_plural = "Political parties"


class PartyMember(models.Model):
    person = models.ForeignKey(Person)
    party = models.ForeignKey(PoliticalParty)
    joined = models.DateField(blank=True, null=True)
    left = models.DateField(blank=True, null=True)

    def __str__(self):
        return str(self.person) + ' (' + str(self.party) + ')'
