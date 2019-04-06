import logging
import requests

import lxml.html
import lxml.etree

logger = logging.getLogger(__name__)


def get_kamervraag_antwoord_ids(kamervraag_url):
    logger.info('get related antwoord id for url: ' + kamervraag_url)
    page = requests.get(kamervraag_url, timeout=60)
    tree = lxml.html.fromstring(page.content)
    elements = tree.xpath('/html/head/meta[@name="OVERHEIDop.aanhangsel"]')
    overheidnl_document_ids = [element.get('content') for element in elements]
    return overheidnl_document_ids


def get_html_content(document_id):
    url = 'https://zoek.officielebekendmakingen.nl/{}.html'.format(document_id)
    response = requests.get(url, timeout=60)
    tree = lxml.html.fromstring(response.content)
    elements = tree.xpath('//div[@class="stuk"]')
    if not elements:
        elements = tree.xpath('//div[contains(@class, "stuk")]')
    if not elements:
        logger.error('no document content found for document url: ' + url)
        elements = tree.xpath('//main[@class="global-main"]')
    html_content = lxml.etree.tostring(elements[0])
    # print('get_html_content', html_content)
    return html_content


def get_metadata(document_id):
    logger.info('get metadata url for document id: ' + str(document_id))
    url = 'https://zoek.officielebekendmakingen.nl/{}'.format(document_id)
    response = requests.get(url, timeout=60)  # get redirected urls (new document ids)
    xml_url = response.url + '/metadata.xml'
    logger.info('get metadata url: ' + xml_url)
    page = requests.get(xml_url, timeout=60)
    tree = lxml.etree.fromstring(page.content)
    attributes_transtable = {
        'DC.type': 'types',
        'OVERHEIDop.dossiernummer': 'dossier_ids',
        'DC.title': 'title_full',
        'OVERHEIDop.documenttitel': 'title_short',
        'OVERHEIDop.indiener': 'submitter',
        'OVERHEIDop.ontvanger': 'receiver',
        'OVERHEIDop.ondernummer': 'id_sub',
        'OVERHEIDop.publicationName': 'publication_type',
        'DCTERMS.issued': 'date_published',
        'DCTERMS.available': 'date_available',
        'OVERHEIDop.datumBrief': 'date_letter_sent',
        'OVERHEIDop.datumIndiening': 'date_submitted',
        'OVERHEIDop.datumOntvangst': 'date_received',
        'OVERHEIDop.datumVergadering': 'date_meeting',
        'OVERHEID.organisationType': 'organisation_type',
        'OVERHEID.category': 'category',
        'DC.creator': 'publisher',
        "OVERHEIDop.vergaderjaar": 'vergaderjaar',
        "OVERHEIDop.vraagnummer": 'vraagnummer',
        "OVERHEIDop.aanhangsel": 'aanhangsel',
        "DC.identifier": 'overheidnl_document_id',
    }

    metadata = {}
    for key, name in attributes_transtable.items():
        elements = tree.xpath('/metadata_gegevens/metadata[@name="{}"]'.format(key))
        if not elements:
            # logger.warning('' + key + ' was not found')
            metadata[name] = ''
            continue
        if len(elements) > 1:
            # if name == 'category' or name == 'submitter':
            metadata[name] = ''
            for element in elements:
                if metadata[name]:
                    metadata[name] += '|'
                metadata[name] += element.get('content')
        else:
            metadata[name] = elements[0].get('content')

    if not metadata['title_short']:
        elements = tree.xpath('/metadata_gegevens/metadata[@name="DC.type"]')
        if elements:
            metadata['title_short'] = elements[0].get('content')

    metadata['is_kamerstuk'] = False
    elements = tree.xpath('/metadata_gegevens/metadata[@name="DC.type"]')
    for element in elements:
        if element.get('scheme') == 'OVERHEIDop.Parlementair':
            metadata['is_kamerstuk'] = element.get('content') == 'Kamerstuk'

    """ agenda code """
    metadata['is_agenda'] = False
    elements = tree.xpath('/metadata_gegevens/metadata[@name="DC.type"]')
    for element in elements:
        if element.get('scheme') == 'OVERHEIDop.Parlementair':
            metadata['is_agenda'] = element.get('content') == 'Agenda'
            
    elements = tree.xpath('/metadata_gegevens/metadata[@name="OVERHEIDop.behandeldDossier"]')
    metadata['behandelde_dossiers'] = [] 
    for element in elements:
        metadata['behandelde_dossiers'].append(element.get('content'))

    logger.info('get metadata url for document id: ' + str(document_id) + ' - END')
    return metadata


def search_politieknl_dossier(dossier_id):
    dossier_url = 'https://zoek.officielebekendmakingen.nl/resultaten'
    document_ids = []
    pagnr = 1
    max_pages = 10
    while pagnr < max_pages:
        logger.info('reading page: ' + str(pagnr))
        params = {
            'pagina': pagnr,
            'q': '(dossiernummer="{}")'.format(dossier_id),
            'pg': 100
        }
        pagnr += 1
        response = requests.get(dossier_url, params, timeout=60)
        tree = lxml.html.fromstring(response.content)
        li_elements = tree.xpath('//ol[@id="PublicatieList"]/li')
        if not li_elements:
            break
        for list_element in li_elements:
            document_link = list_element.xpath('div[@class="result-item"]/a')[0]
            relative_url = document_link.get('href')
            document_id = relative_url.replace('/', '').replace('.html', '')
            document_ids.append(document_id)
    return document_ids
