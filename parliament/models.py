import logging
import datetime

from django.db import models
from django.utils.functional import cached_property
from django.utils.text import slugify

from wikidata import wikidata

from person.models import Person

logger = logging.getLogger(__name__)


class Parliament(models.Model):
    name = models.CharField(max_length=200)
    wikidata_id = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return str(self.name)

    def get_members_at_date(self, check_date):
        members = self.members
        members_active = members.filter(joined__lt=check_date, left__gte=check_date) | members.filter(joined__lt=check_date, left=None)
        return members_active

    @cached_property
    def members(self):
        return ParliamentMember.objects.filter(parliament=self)

    @staticmethod
    def get_or_create_tweede_kamer():
        parliaments = Parliament.objects.filter(name='Tweede Kamer')
        if parliaments.exists():
            return parliaments[0]
        else:
            return Parliament.objects.create(name='Tweede Kamer', wikidata_id='Q233262')


class ParliamentMember(models.Model):
    person = models.ForeignKey(Person)
    parliament = models.ForeignKey(Parliament)
    joined = models.DateField(blank=True, null=True)
    left = models.DateField(blank=True, null=True)

    @staticmethod
    def find(surname, initials=''):
        logger.info('surname: ' + surname + ', initials: ' + initials)
        person = Person.find_surname_initials(surname, initials)
        members = ParliamentMember.objects.filter(person=person)
        if members.exists():
            return members[0]
        logger.info('ParliamentMember not found.')
        return None

    def party(self):
        memberships = PartyMember.objects.filter(person=self.person)
        for member in memberships:
            if member.left is None:
                return member.party
        return None

    def check_overlap(self):
        members = ParliamentMember.objects.filter(person=self.person)
        if members.count() <= 1:
            return []
        overlapping_members = []
        for member_a in members:
            for member_b in members:
                if member_a.id == member_b.id or not member_a.joined or not member_b.joined:
                    continue
                left_a = datetime.date.today() + datetime.timedelta(days=1)
                left_b = datetime.date.today() + datetime.timedelta(days=1)
                if member_a.left:
                    left_a = member_a.left
                if member_b.left:
                    left_b = member_b.left
                if member_a.joined < member_b.joined < left_a:
                    overlapping_members.append(member_a)
                elif member_b.joined < member_a.joined < left_b:
                    overlapping_members.append(member_a)
                elif member_b.joined < member_a.joined and left_a < left_b:
                    overlapping_members.append(member_a)
                elif member_a.joined < member_b.joined and left_b < left_a:
                    overlapping_members.append(member_a)
        return overlapping_members

    def __str__(self):
        display_name = self.person.fullname()
        party = self.party()
        if party:
            display_name += ' (' + str(party.name_short) + ')'
        return display_name


class PoliticalParty(models.Model):
    name = models.CharField(max_length=200)
    name_short = models.CharField(max_length=10)
    founded = models.DateField(blank=True, null=True)
    dissolved = models.DateField(blank=True, null=True)
    wikidata_id = models.CharField(max_length=200, blank=True)
    wikimedia_logo_url = models.URLField(blank=True)
    wikipedia_url = models.URLField(blank=True)
    official_website_url = models.URLField(blank=True)
    slug = models.SlugField(max_length=250, default='')

    def __str__(self):
        return str(self.name) + ' (' + str(self.name_short) + ')'

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name_short)
        super().save(*args, **kwargs)

    @cached_property
    def members_current(self):
        return PartyMember.objects.filter(party=self, left=None)

    def find_wikidata_id(self, language='en', top_level_domain='com'):
        wikidata_ids = wikidata.search_wikidata_ids(self.name, language)
        if not wikidata_ids:
            return ''
        # find the first result with a website with the given domain
        for wid in wikidata_ids:
            official_website = wikidata.WikidataItem(wid).get_official_website()
            if official_website:
                tld = official_website.split('.')[-1]
                if tld == top_level_domain or tld == top_level_domain + '/':
                    return wid
        return wikidata_ids[0]

    def update_info(self, language='en', top_level_domain='com'):
        """
        update the model derived info
        :param language: the language to search for in wikidata
        :param top_level_domain: the top level domain of the party website, also used to determine country
        """
        if top_level_domain[0] == '.':
            logger.warning("Top level domain should not start with a dot (use 'com' instead of '.com')" )
        if not self.wikidata_id:
            self.wikidata_id = self.find_wikidata_id(language, top_level_domain)
            if not self.wikidata_id:
                return
        wikidata_item = wikidata.WikidataItem(self.wikidata_id)
        self.official_website_url = wikidata_item.get_official_website()
        self.wikipedia_url = wikidata_item.get_wikipedia_url(language)
        logger.info(self.name + ' - id: ' + str(self.wikidata_id) + ', website: ' + str(self.official_website_url))
        logo_filename = wikidata_item.get_logo_filename()
        self.founded = wikidata_item.get_inception()
        if logo_filename:
            self.wikimedia_logo_url = wikidata.WikidataItem.get_wikimedia_image_url(logo_filename)
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

    class Meta:
        verbose_name_plural = "Political parties"


class PartyMember(models.Model):
    person = models.ForeignKey(Person, related_name='partymember')
    party = models.ForeignKey(PoliticalParty)
    joined = models.DateField(blank=True, null=True)
    left = models.DateField(blank=True, null=True)

    def __str__(self):
        return str(self.person) + ' (' + str(self.party) + ')'
