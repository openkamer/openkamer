import logging
import re

import requests
import lxml.html

logger = logging.getLogger(__name__)


def search_parties():
    logger.info('START')
    url = 'https://www.tweedekamer.nl/kamerleden/fracties'
    page = requests.get(url, timeout=60)
    tree = lxml.html.fromstring(page.content)
    rows = tree.xpath("//ul[@class='reset grouped-list']/li/a")
    parties = []
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
        party = {
            'name': name,
            'name_short': name_short,
        }
        parties.append(party)
    logger.info('END')
    return parties
