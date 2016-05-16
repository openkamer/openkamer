from django.db import models

from wikidata import wikidata

from person.models import Person


class Parliament(models.Model):
    name = models.CharField(max_length=200)
    wikidata_id = models.CharField(max_length=200, blank=True)

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
    name_short = models.CharField(max_length=10)
    founded = models.DateField(blank=True, null=True)
    dissolved = models.DateField(blank=True, null=True)
    logo = models.ImageField(blank=True)
    wikidata_id = models.CharField(max_length=200, blank=True)
    wikimedia_logo_url = models.URLField(blank=True)
    wikipedia_url = models.URLField(blank=True)

    def __str__(self):
        return str(self.name) + ' (' + str(self.name_short) + ')'

    def update_info(self, language='en'):
        wikidata_id = wikidata.search_wikidata_id(self.name, language)
        if not wikidata_id:
            return
        print(self.name + ' - id: ' + wikidata_id)
        self.wikidata_id = wikidata_id
        logo_filename = wikidata.get_logo_filename(self.wikidata_id)
        if logo_filename:
            self.wikimedia_logo_url = wikidata.get_wikimedia_image_url(logo_filename)

    @staticmethod
    def find_party(name):
        parties = PoliticalParty.objects.filter(name=name)
        if parties.exists():
            return parties[0]
        parties = PoliticalParty.objects.filter(name_short=name)
        if parties.exists():
            return parties[0]
        return None

    @staticmethod
    def get_or_create_party(party_name):
        party = PoliticalParty.objects.filter(name=party_name)
        if party.exists():
            return party[0]
        party = PoliticalParty.objects.filter(name_short=party_name)
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
