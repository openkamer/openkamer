import logging
import re

import requests
import lxml.html

from parliament.models import PoliticalParty

logger = logging.getLogger(__name__)


def create_parties():
    logger.info('START')
    url = 'https://www.tweedekamer.nl/kamerleden/fracties'
    page = requests.get(url)
    tree = lxml.html.fromstring(page.content)

    rows = tree.xpath("//ul[@class='reset grouped-list']/li/a")
    for row in rows:
        columns = row.text.split('-')
        if len(columns) > 1:
            name = columns[0].strip()
            name_short = columns[1]
            name_short = re.sub(r'\(.+?\)', '', name_short).strip()
        else:
            name = columns[0]
            name = re.sub(r'\(.+?\)', '', name).strip()
            name_short = name
        party = PoliticalParty.find_party(name)
        if party:
            logger.warning('party ' + name + ' already exists!')
        else:
            party = PoliticalParty.objects.create(name=name, name_short=name_short)
            logger.info('created: ' + str(party))
        party.update_info('nl', 'nl')
        party.save()
    logger.info('END')
