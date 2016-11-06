import requests
import logging

import lxml.html

from wikidata import wikidata

from person.models import Person
from parliament.models import Parliament
from parliament.models import PoliticalParty
from parliament.models import PartyMember
from parliament.models import ParliamentMember

logger = logging.getLogger(__name__)


def create_members():
    url = 'http://www.tweedekamer.nl/kamerleden/alle_kamerleden'
    page = requests.get(url)
    tree = lxml.html.fromstring(page.content)

    parliament = Parliament.get_or_create_tweede_kamer()

    rows = tree.xpath("//tbody/tr")

    for row in rows:
        columns = row.xpath("td")
        if len(columns) == 8:
            forename = columns[1][0].text
            surname = columns[0][0].text.split(',')[0]
            prefix = columns[0][0].text.split('.')[-1].strip()
            initials = columns[0][0].text.split(',')[1].replace(prefix, '').replace(' ', '')
            if Person.person_exists(forename, surname):
                person = Person.objects.get(forename=forename, surname=surname)
            else:
                person = Person.objects.create(
                    forename=forename,
                    surname=surname,
                    surname_prefix=prefix,
                    initials=initials
                )
            party_name = columns[2][0].text
            party = PoliticalParty.get_party(party_name)
            party_member = PartyMember.objects.create(person=person, party=party)
            parliament_member = ParliamentMember.objects.create(person=person, parliament=parliament)
            logger.info("new person: " + str(person))
            logger.info("new party member: " + str(party_member))
            logger.info("new parliament member: " + str(parliament_member))
