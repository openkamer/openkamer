import logging

from django.db import transaction

from tkapi import TKApi
from tkapi.persoon import PersoonReis

from person.models import Person
from travel.models import Travel, TravelPersonPosition

logger = logging.getLogger(__name__)


@transaction.atomic
def create_travels(max_items=None):
    travels = TKApi.get_items(PersoonReis, max_items=max_items)
    logger.info('{} travels found.'.format(len(travels)))
    if len(travels) < 1000:
        logger.error('Only {} travels found. This is unexpected. Skip re-creating travels.'.format(len(travels)))
    Travel.objects.all().delete()
    TravelPersonPosition.objects.all().delete()
    for travel in travels:
        person = Person.find_surname_initials(travel.persoon.achternaam, travel.persoon.initialen)
        if person is None:
            logger.warning('No person found for travel: {}'.format(travel.id))
            continue
        if travel.van is None or travel.tot_en_met is None:
            logger.warning('No date found for travel: {}'.format(travel.id))
            continue
        Travel.objects.create(
            person=person,
            destination=travel.bestemming,
            purpose=travel.doel,
            paid_by=travel.betaald_door,
            date_begin=travel.van,
            date_end=travel.tot_en_met,
        )
