import logging
import requests

import lxml

logger = logging.getLogger(__name__)


def search_dossier_url(dossier_id):
    url = 'https://www.tweedekamer.nl/zoeken'
    params = {
        'qry': str(dossier_id),
        'Type': 'Wetsvoorstellen'
    }
    response = requests.get(url, params)
    tree = lxml.html.fromstring(response.content)
    elements = tree.xpath('//div[@class="search-result-content"]/h3/a')
    if elements:
        return 'https://www.tweedekamer.nl' + elements[0].attrib['href']
    return ''


def get_dossier_decision(dossier_url):
    response = requests.get(dossier_url)
    tree = lxml.html.fromstring(response.content)
    elements = tree.xpath('//div[@class="bill-header"]/p[@class="status"]/span')
    if elements:
        return elements[0].text
    return ''


def get_dossier_ids_wetsvoorstellen_initiatief(max_results=None, filter_active=False, filter_inactive=False):
    logger.info('BEGIN')
    dossier_ids = get_wetsvoorstellen_dossier_ids('Initiatiefwetsvoorstellen', max_results, filter_active, filter_inactive)
    logger.info('END')
    return dossier_ids


def get_dossier_ids_wetsvoorstellen_regering(max_results=None, filter_active=False, filter_inactive=False):
    logger.info('BEGIN')
    dossier_ids = get_wetsvoorstellen_dossier_ids('Wetsvoorstellen+regering', max_results, filter_active, filter_inactive)
    logger.info('END')
    return dossier_ids


def get_wetsvoorstellen_dossier_ids(subsubcategorie, max_results=None, filter_active=False, filter_inactive=False):
    logger.info('BEGIN')
    assert not (filter_active and filter_inactive)
    url = 'https://www.tweedekamer.nl/kamerstukken/wetsvoorstellen'
    # these parameters cannot be percent encoded, and can thus not be part of the params variable
    url += '?clusterName=' + subsubcategorie + '&fld_tk_subsubcategorie=' + subsubcategorie
    params = {
        'qry': '*',
        'fld_tk_categorie': 'Kamerstukken',
        'fld_tk_subcategorie': 'Wetsvoorstellen',
        'srt': 'date;desc;date',
        'Type': 'Wetsvoorstellen',
        'sta': '1'
    }
    if filter_active:
        params['fld_prl_status'] = 'Aanhangig'
    if filter_inactive:
        params['fld_prl_status'] = 'Afgedaan'
    dossier_ids = []
    new_dossiers_found = True
    start = 1
    while new_dossiers_found:
        logger.info('start item nr: ' + str(start))
        params['sta'] = str(start)
        response = requests.get(url, params)
        response.raise_for_status()
        tree = lxml.html.fromstring(response.content)
        elements = tree.xpath('//div[@class="search-result-properties"]/p')
        logger.info('results on page: ' + str(len(elements)/2))
        new_dossiers_found = len(elements) != 0
        if not new_dossiers_found:
            logger.info('no new dossiers found on page: ' + str(response.url))
        for element in elements:
            if 'class' not in element.attrib:
                dossier_ids.append(element.text.split('-')[0])  # A 'Rijkswet' has the format '34158-(R2048)', removing the last part because there is no use for it (yet)
                start += 1
                if max_results and len(dossier_ids) >= max_results:
                    logger.info('END: max results reached')
                    return dossier_ids
    logger.info('END')
    return dossier_ids
