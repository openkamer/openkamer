import logging

from django.db import models

from wikidata import wikidata

from person.models import Person

logger = logging.getLogger(__name__)


class Government(models.Model):
    name = models.CharField(max_length=200)
    date_formed = models.DateField()
    wikidata_id = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return str(self.name)


class Ministry(models.Model):
    name = models.CharField(max_length=200)
    government = models.ForeignKey(Government)


class GovernmentPosition(models.Model):
    MINISTER = 'MIN'
    SECRETARY_OF_STATE = 'SOS'
    PRIME_MINISTER = 'PMI'
    DEPUTY_PRIME_MINISTER = 'DPM'
    GOVERNMENT_POSITIONS = (
        (MINISTER, 'Minister'),
        (SECRETARY_OF_STATE, 'Secretary of State'),
        (PRIME_MINISTER, 'Prime Minister'),
        (DEPUTY_PRIME_MINISTER, 'Deputy Prime Minister'),
    )
    position = models.CharField(max_length=3, choices=GOVERNMENT_POSITIONS)
    ministry = models.ForeignKey(Ministry, blank=True, null=True)

    def __str__(self):
        return self.get_position_display()

    @staticmethod
    def find_position_type(position_str):
        position_str = position_str.lower()
        if 'vice' and 'minister' and 'president' in position_str:
            return GovernmentPosition.DEPUTY_PRIME_MINISTER
        elif 'minister' and 'president' in position_str:
            return GovernmentPosition.PRIME_MINISTER
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
