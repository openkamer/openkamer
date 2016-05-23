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

    def party(self):
        memberships = PartyMember.objects.filter(person=self.person)
        if memberships:
            assert memberships.count() == 1
            return memberships[0].party
        return None

    def __str__(self):
        return str(self.person) + ' (' + str(self.parliament) + ')'


class PoliticalParty(models.Model):
    name = models.CharField(max_length=200)
    name_short = models.CharField(max_length=10)
    founded = models.DateField(blank=True, null=True)
    dissolved = models.DateField(blank=True, null=True)
    wikidata_id = models.CharField(max_length=200, blank=True)
    wikimedia_logo_url = models.URLField(blank=True)
    wikipedia_url = models.URLField(blank=True)
    official_website_url = models.URLField(blank=True)

    def __str__(self):
        return str(self.name) + ' (' + str(self.name_short) + ')'

    def update_info(self, language='en', top_level_domain='com'):
        """
        update the model derived info
        :param language: the language to search for in wikidata
        :param top_level_domain: the top level domain of the party website, also used to determine country
        """
        if top_level_domain[0] == '.':
            print("Warning: top level domain should not start with a dot (use 'com' instead of '.com')" )
        wikidata_ids = wikidata.search_wikidata_ids(self.name, language)
        if not wikidata_ids:
            return
        wikidata_id = wikidata_ids[0]
        # find the first result with a website with the given domain
        for id in wikidata_ids:
            official_website = wikidata.get_official_website(id)
            if official_website:
                tld = official_website.split('.')[-1]
                if tld == top_level_domain or tld == top_level_domain + '/':
                    self.official_website_url = official_website
                    wikidata_id = id
                    break
        self.wikidata_id = wikidata_id
        self.wikipedia_url = wikidata.get_wikipedia_url(wikidata_id, language)
        print(self.name + ' - id: ' + self.wikidata_id + ', website: ' + self.official_website_url)
        logo_filename = wikidata.get_logo_filename(self.wikidata_id)
        inception_date = wikidata.get_inception(self.wikidata_id)
        if inception_date:
            print(inception_date)
            self.founded = inception_date
        if logo_filename:
            self.wikimedia_logo_url = wikidata.get_wikimedia_image_url(logo_filename)
        self.save()

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
    def get_party(party_name):
        party = PoliticalParty.objects.filter(name=party_name)
        if party.exists():
            return party[0]
        party = PoliticalParty.objects.filter(name_short=party_name)
        if party.exists():
            return party[0]
        return None

    class Meta:
        verbose_name_plural = "Political parties"


class PartyMember(models.Model):
    person = models.ForeignKey(Person, related_name='partymember')
    party = models.ForeignKey(PoliticalParty)
    joined = models.DateField(blank=True, null=True)
    left = models.DateField(blank=True, null=True)

    def __str__(self):
        return str(self.person) + ' (' + str(self.party) + ')'