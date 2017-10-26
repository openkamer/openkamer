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


def get_dossier_decision(dossier_url):
    response = requests.get(dossier_url, timeout=60)
    tree = lxml.html.fromstring(response.content)
    elements = tree.xpath('//div[@class="bill-header"]/p[@class="status"]/span')
    if elements:
        return elements[0].text
    return ''


def get_number_of_wetsvoorstellen():
    url = 'https://www.tweedekamer.nl/kamerstukken/wetsvoorstellen/?qry=%2A&fld_tk_categorie=Kamerstukken&fld_tk_subcategorie=Wetsvoorstellen&Type=Wetsvoorstellen&srt=date%3Adesc%3Adate'
    response = requests.get(url, timeout=60)
    result = re.search("Wetsvoorstellen regering \((\d+)\)", response.content.decode('utf-8'))
    number_regering = int(result.group(1))
    result = re.search("Initiatiefwetsvoorstellen \((\d+)\)", response.content.decode('utf-8'))
    number_initiatief = int(result.group(1))
    return number_initiatief, number_regering
