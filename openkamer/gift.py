import logging
import re

from django.db import transaction

from tkapi import TKApi
from tkapi.persoon import PersoonGeschenk

from person.models import Person
from gift.models import Gift, PersonPosition

logger = logging.getLogger(__name__)


@transaction.atomic
def create_gifts(max_items=None):
    gifts = TKApi.get_items(PersoonGeschenk, max_items=max_items)
    logger.info('{} gifts found.'.format(len(gifts)))
    if len(gifts) < 1000:
        logger.error('Only {} gifts found. This is unexpected. Skip re-creating gifts.'.format(len(gifts)))
    Gift.objects.all().delete()
    PersonPosition.objects.all().delete()
    for gift in gifts:
        value = find_gift_value(gift.omschrijving)
        gift_type = find_gift_type(gift.omschrijving)
        person = Person.find_surname_initials(gift.persoon.achternaam, gift.persoon.initialen)
        if person is None:
            logger.warning('No person found for gift: {}'.format(gift.id))
            continue
        if gift.datum is None:
            logger.warning('No date found for gift: {}'.format(gift.id))
            continue
        Gift.objects.create(
            person=person,
            value_euro=value,
            description=gift.omschrijving,
            date=gift.datum,
            type=gift_type,
        )


def find_gift_value(text):
    matches = re.findall(r'€\s*(\d+)[,*|.*](\d*)', text)
    if matches is None:
        return None
    values = []
    for match in matches:
        value = match[0]
        if match[1]:
            value += '.{}'.format(match[1])
        values.append(float(value))
    if not values:
        return None
    value = max(values)
    return value


def find_gift_type(text):
    text = text.lower()
    if 'boek' in text:
        return Gift.BOEK
    if 'wijn' in text or 'champagne' in text:
        return Gift.WIJN
    if 'kaart' in text or 'toegangsbewijzen' in text or 'toegangsbewijs' in text or 'concert' in text \
        or 'ticket' in text or 'een uitnodiging' in text:
        return Gift.TOEGANGSKAART
    if 'bloem' in text:
        return Gift.BLOEMEN
    if 'sjaal' in text or 'stropdas' in text or 'sokken' in text:
        return Gift.KLEDING
    if 'pakket' in text:
        return Gift.PAKKET
    if 'lunch' in text or 'diner' in text or 'ontbijt' in text:
        return Gift.DINER
    return Gift.ONBEKEND
