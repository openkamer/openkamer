import datetime
import logging

from django.db import models
from django.utils.text import slugify

from person.models import Person

logger = logging.getLogger(__name__)


class Government(models.Model):
    name = models.CharField(max_length=200)
    date_formed = models.DateField()
    date_dissolved = models.DateField(blank=True, null=True)
    wikidata_id = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(max_length=250, default='')

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def prime_minister(self):
        pms = GovernmentPosition.objects.filter(
            position=GovernmentPosition.PRIME_MINISTER,
            government=self
        )
        if pms.exists():
            return pms[0].member_latest()
        return None

    def deputy_prime_minister(self):
        deputies = GovernmentPosition.objects.filter(
            position=GovernmentPosition.DEPUTY_PRIME_MINISTER,
            government=self
        )
        if deputies.exists():
            return deputies[0].member_latest()
        return None

    def members_latest(self):
        member_ids = []
        positions = GovernmentPosition.objects.filter(government=self)
        for position in positions:
            member_ids.append(position.member_latest().id)
        return GovernmentMember.objects.filter(pk__in=member_ids)

    def members(self):
        member_ids = []
        positions = GovernmentPosition.objects.filter(government=self)
        for position in positions:
            member_ids += [member.id for member in position.members()]
        return GovernmentMember.objects.filter(pk__in=member_ids)

    def ministers_without_portfolio_current(self):
        member_ids = []
        positions = GovernmentPosition.objects.filter(government=self, position=GovernmentPosition.MINISTER_WO_PORTFOLIO)
        for position in positions:
            member_ids.append(position.member_latest().id)
        return GovernmentMember.objects.filter(pk__in=member_ids)

    def ministries(self):
        return Ministry.objects.filter(government=self)

    def __str__(self):
        return str(self.name)


class Ministry(models.Model):
    name = models.CharField(max_length=200)
    government = models.ForeignKey(Government)

    def positions(self):
        return GovernmentPosition.objects.filter(ministry=self)

    def has_members_replaced(self):
        positions = GovernmentPosition.objects.filter(ministry=self)
        for position in positions:
            if position.members_replaced().exists():
                return True
        return False

    def __str__(self):
        return str(self.name)


class GovernmentPosition(models.Model):
    MINISTER = 'MIN'
    MINISTER_WO_PORTFOLIO = 'MWP'
    SECRETARY_OF_STATE = 'SOS'
    PRIME_MINISTER = 'PMI'
    DEPUTY_PRIME_MINISTER = 'DPM'
    GOVERNMENT_POSITIONS = (
        (MINISTER, 'Minister'),
        (MINISTER_WO_PORTFOLIO, 'Minister zonder portefeuille'),
        (SECRETARY_OF_STATE, 'Staatssecretaris'),
        (PRIME_MINISTER, 'Minister-president'),
        (DEPUTY_PRIME_MINISTER, 'Viceminister-president'),
    )
    position = models.CharField(max_length=3, choices=GOVERNMENT_POSITIONS)
    ministry = models.ForeignKey(Ministry, blank=True, null=True)
    government = models.ForeignKey(Government, blank=True, null=True)
    extra_info = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.get_position_display()

    def member_latest(self):
        current = GovernmentMember.objects.filter(position=self, end_date__isnull=True)
        if current:
            return current[0]
        else:
            return GovernmentMember.objects.filter(position=self).order_by('-end_date')[0]

    def members_replaced(self):
        latest_date = self.government.date_dissolved
        if not latest_date:
            latest_date = datetime.date.today()
        return GovernmentMember.objects.filter(position=self, end_date__lt=latest_date)

    def members(self):
        return GovernmentMember.objects.filter(position=self)

    @staticmethod
    def find_position_type(position_str):
        logger.info(position_str)
        position_str = position_str.lower()
        if 'viceminister-president' in position_str:
            return GovernmentPosition.DEPUTY_PRIME_MINISTER
        elif 'minister-president' in position_str:
            return GovernmentPosition.PRIME_MINISTER
        elif 'minister zonder portefeuille' in position_str:
            return GovernmentPosition.MINISTER_WO_PORTFOLIO
        elif 'minister' in position_str:
            return GovernmentPosition.MINISTER
        elif 'staatssecretaris' in position_str:
            return GovernmentPosition.SECRETARY_OF_STATE
        return ''


class GovernmentMember(models.Model):
    person = models.ForeignKey(Person)
    position = models.ForeignKey(GovernmentPosition)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return str(self.person) + ' as ' + str(self.position)

    def is_active(self):
        return self.end_date is None
