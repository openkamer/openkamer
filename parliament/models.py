import logging
import datetime

from unidecode import unidecode

from django.db import models
from django.utils.functional import cached_property
from django.utils.text import slugify

from wikidata import wikidata

from person.models import Person

logger = logging.getLogger(__name__)


class Parliament(models.Model):
    name = models.CharField(max_length=200)
    wikidata_id = models.CharField(max_length=200, blank=True)

    TWEEDE_KAMER_WIKIDATA_ID = 'Q233262'

    def __str__(self):
        return str(self.name)

    def get_members_at_date(self, check_date):
        members = self.members
        members_active = members.filter(joined__lte=check_date, left__gt=check_date) | members.filter(joined__lte=check_date, left=None)
        return members_active.order_by('person__surname')

    @cached_property
    def members(self):
        return ParliamentMember.objects.filter(parliament=self).select_related('person', 'parliament')

    @staticmethod
    def get_or_create_tweede_kamer():
        parliaments = Parliament.objects.filter(name='Tweede Kamer')
        if parliaments.exists():
            return parliaments[0]
        else:
            return Parliament.objects.create(name='Tweede Kamer', wikidata_id=Parliament.TWEEDE_KAMER_WIKIDATA_ID)


class ParliamentMember(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    parliament = models.ForeignKey(Parliament, on_delete=models.CASCADE)
    joined = models.DateField(blank=True, null=True, db_index=True)
    left = models.DateField(blank=True, null=True, db_index=True)

    @staticmethod
    def find(surname, initials='', date=None):
        person = Person.find_surname_initials(surname, initials)
        if date:
            members = ParliamentMember.find_at_date(person, date)
        else:
            members = ParliamentMember.objects.filter(person=person).order_by('-joined')
        if members.exists():
            return members[0]
        logger.info('ParliamentMember not found for: {} ({})'.format(surname, initials))
        return None

    @staticmethod
    def find_at_date(person, date):
        return ParliamentMember.objects.filter(person=person, joined__lte=date, left__gt=date) | \
               ParliamentMember.objects.filter(person=person, joined__lte=date, left__isnull=True)

    @staticmethod
    def active_at_date(date):
        return ParliamentMember.objects.filter(joined__lte=date, left__gt=date) | \
               ParliamentMember.objects.filter(joined__lte=date, left__isnull=True)

    def party_memberships(self):
        memberships = PartyMember.objects.filter(person=self.person)
        if self.left:
            memberships = memberships.exclude(joined__gte=self.left)
        if self.joined:
            memberships = memberships.exclude(left__lte=self.joined)
        if memberships.count() == 1:
            memberships = memberships
        elif self.joined and self.left:
            memberships = PartyMember.objects.filter(person=self.person, joined__lte=self.joined, left__gte=self.left)
        elif self.joined:
            memberships = PartyMember.objects.filter(person=self.person, joined__lte=self.joined, left__isnull=True)
        else:
            logger.error('multiple or no parties for ' + str(self.person) + ' found without joined/end date')
        return memberships

    def political_parties(self):
        memberships = self.party_memberships()
        party_ids = []
        for member in memberships:
            party_ids.append(member.party.id)
        return PoliticalParty.objects.filter(id__in=party_ids)

    def political_party(self):
        memberships = self.party_memberships().order_by('-joined')
        if memberships:
            return memberships[0].party
        return None

    @cached_property
    def party(self):
        return self.political_party()

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

    def __html__(self):
        display_name = self.person.fullname()
        party = self.political_party()  # do not use the cached_property here because this might fail tests during creation phase
        if party:
            display_name += ' (' + str(party.name_short) + ')'
        return display_name


class PoliticalParty(models.Model):
    tk_id = models.CharField(max_length=200, blank=True, null=True, db_index=True)
    name = models.CharField(max_length=200)
    name_short = models.CharField(max_length=200)
    founded = models.DateField(blank=True, null=True)
    dissolved = models.DateField(blank=True, null=True)
    wikidata_id = models.CharField(max_length=200, blank=True)
    wikimedia_logo_url = models.URLField(blank=True, max_length=1000)
    wikipedia_url = models.URLField(blank=True, max_length=1000)
    official_website_url = models.URLField(blank=True, max_length=1000)
    slug = models.SlugField(max_length=250, default='', db_index=True)
    current_parliament_seats = models.IntegerField(default=0)

    def __str__(self):
        name = self.name_short
        if self.name_short != self.name:
            name += ' (' + str(self.name) + ')'
        return name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name_short)
        super().save(*args, **kwargs)

    @cached_property
    def members_current(self):
        return PartyMember.objects.filter(party=self, left=None)

    @cached_property
    def members_current_unique_person(self):
        person_ids = []
        member_ids = []
        for member in self.members_current:
            if member.person.id not in person_ids:
                member_ids.append(member.id)
                person_ids.append(member.person.id)
        return PartyMember.objects.filter(id__in=member_ids).order_by('person__surname')

    @staticmethod
    def sort_by_current_seats(parties):
        return sorted(parties, key=lambda party: party.current_parliament_seats, reverse=True)

    def set_current_parliament_seats(self):
        self.current_parliament_seats = self.parliament_members_current.count()
        logger.info(self.name + ': ' + str(self.current_parliament_seats))
        self.save()

    @cached_property
    def parliament_members_current(self):
        parliament_members = Parliament.get_or_create_tweede_kamer().get_members_at_date(datetime.date.today()).select_related('person')
        pm_ids = []
        for member in parliament_members:
            if member.party and member.party.id == self.id:
                pm_ids.append(member.id)
        return ParliamentMember.objects.filter(id__in=pm_ids)

    @cached_property
    def total_parliament_members(self):
        parties = PoliticalParty.objects.all()
        count = 0
        for party in parties:
            count += party.current_parliament_seats
        return count

    def find_wikidata_id(self, language='nl'):
        return wikidata.search_political_party_id(self.name, language=language)

    def update_info(self, language='nl'):
        """
        update the party with wikidata info
        :param language: the language to search for in wikidata
        """
        logger.info('update party info for {}'.format(self.name))
        if not self.wikidata_id:
            self.wikidata_id = self.find_wikidata_id(language)
            if not self.wikidata_id:
                logger.warning('no wikidata_id found for {}'.format(self.name))
                return
        wikidata_item = wikidata.WikidataItem(self.wikidata_id)
        self.official_website_url = wikidata_item.get_official_website()
        self.wikipedia_url = wikidata_item.get_wikipedia_url(language)
        logger.info(self.name + ' - id: ' + str(self.wikidata_id))
        logo_filename = wikidata_item.get_logo_filename()
        self.founded = wikidata_item.get_inception()
        if not self.name_short and wikidata_item.get_short_name():
            self.name_short = wikidata_item.get_short_name()
        if logo_filename:
            self.wikimedia_logo_url = wikidata.WikidataItem.get_wikimedia_image_url(logo_filename)
        self.save()

    @staticmethod
    def find_party(name):
        name_ascii = unidecode(name)
        name_lid = 'Lid-' + name
        name_no_dash = name.replace('-', ' ')
        parties = PoliticalParty.objects.filter(name__iexact=name) \
                  | PoliticalParty.objects.filter(name__iexact=name_ascii) \
                  | PoliticalParty.objects.filter(name__iexact=name_lid) \
                  | PoliticalParty.objects.filter(name__iexact=name_no_dash)
        if parties.exists():
            return parties[0]
        parties = PoliticalParty.objects.filter(name_short__iexact=name) \
                  | PoliticalParty.objects.filter(name_short__iexact=name_ascii) \
                  | PoliticalParty.objects.filter(name_short__iexact=name_lid) \
                  | PoliticalParty.objects.filter(name_short__iexact=name_no_dash)
        if parties.exists():
            return parties[0]
        logger.warning('party not found: ' + name)
        return None

    class Meta:
        verbose_name_plural = "Political parties"


class PartyMember(models.Model):
    person = models.ForeignKey(Person, related_name='partymember', on_delete=models.CASCADE)
    party = models.ForeignKey(PoliticalParty, on_delete=models.CASCADE)
    joined = models.DateField(blank=True, null=True, db_index=True)
    left = models.DateField(blank=True, null=True, db_index=True)

    @staticmethod
    def get_at_date(person, date):
        return PartyMember.objects.filter(person=person, joined__lte=date, left__gt=date) | \
               PartyMember.objects.filter(person=person, joined__lte=date, left__isnull=True) | \
               PartyMember.objects.filter(person=person, joined__isnull=True, left__gt=date) | \
               PartyMember.objects.filter(person=person, joined__isnull=True, left__isnull=True)

    def __str__(self):
        return str(self.person) + ' (' + str(self.party) + ')'


class Commissie(models.Model):
    name = models.CharField(max_length=500)
    name_short = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, default='', db_index=True)

    def save(self, *args, **kwargs):
        self.name_short = self.create_short_name(str(self.name))
        self.slug = self.create_slug(self.name_short)
        super().save(*args, **kwargs)

    @staticmethod
    def create_short_name(name):
        name = name.replace('vaste commissie voor', '').strip()
        name = name.replace('algemene commissie voor', '').strip()
        return name

    @staticmethod
    def create_slug(name_short):
        return slugify(name_short)

    def __html__(self):
        return self.name_short
