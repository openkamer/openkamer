import logging
import requests
import re
import time

import lxml

logger = logging.getLogger(__name__)


def search_dossier_url(dossier_id):
    url = 'https://www.tweedekamer.nl/zoeken'
    params = {
        'qry': str(dossier_id),
        'Type': 'Wetsvoorstellen'
    }
    response = requests.get(url, params, timeout=60)
    tree = lxml.html.fromstring(response.content)
    elements = tree.xpath('//div[@class="search-result-content"]/h3/a')
    if elements:
        return 'https://www.tweedekamer.nl' + elements[0].attrib['href']
    return ''
