import logging
import datetime
import re

import requests
import lxml
import lxml.html
import lxml.etree

logger = logging.getLogger(__name__)


def get_dossier_ids_wetsvoorstellen_initiatief(max_results=None):
    logger.info('BEGIN')
    dossier_ids = get_wetsvoorstellen_dossier_ids('Initiatiefwetsvoorstellen', max_results)
    logger.info('END')
    return dossier_ids


def get_dossier_ids_wetsvoorstellen_regering(max_results=None):
    logger.info('BEGIN')
    dossier_ids = get_wetsvoorstellen_dossier_ids('Wetsvoorstellen+regering', max_results)
    logger.info('END')
    return dossier_ids


def get_wetsvoorstellen_dossier_ids(subsubcategorie, max_results=None):
    logger.info('BEGIN')
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
    dossier_ids = []
    new_dossiers_found = True
    start = 1
    while new_dossiers_found:
        params['sta'] = str(start)
        page = requests.get(url, params)
        tree = lxml.html.fromstring(page.content)
        elements = tree.xpath('//div[@class="search-result-properties"]/p')
        new_dossiers_found = len(elements) != 0
        for element in elements:
            if 'class' not in element.attrib:
                dossier_ids.append(element.text.split('-')[0])  # A 'Rijkswet' has the format '34158-(R2048)', removing the last part because there is no use for it (yet)
                start += 1
                if max_results and len(dossier_ids) >= max_results:
                    logger.info('END: max results reached')
                    return dossier_ids
    logger.info('END')
    return dossier_ids


def get_document_id_and_content(url):
    logger.info('get document id for url: ' + url)
    page = requests.get(url)
    tree = lxml.html.fromstring(page.content)
    elements = tree.xpath('//ul/li/a[@id="technischeInfoHyperlink"]')
    if elements:
        document_id = elements[0].get('href').split('/')[-1]
    else:
        elements = tree.xpath('/html/head/meta[@name="dcterms.identifier"]')
        if not elements:
            return None, ''
        document_id = elements[0].get('content')
    logger.info('document id: ' + document_id)
    elements = tree.xpath('//div[@class="stuk"]')
    if elements:
        content_html = lxml.etree.tostring(elements[0])
    elif tree.xpath('//h2[@class="stuktitel"]'):
        content_html = lxml.etree.tostring(tree.xpath('//h2[@class="stuktitel"]')[0].getparent())
    else:
        content_html = ''
    titles = tree.xpath('//h2[@class="stuktitel"]')
    titles += tree.xpath('//h1[@class="stuktitel"]')
    title = ''
    if titles:
        text = titles[0].text_content()
        title = re.sub("\w{2}\.\s\d+", '', text).strip().lower()  # remove 'nr. 6'
    return document_id, content_html, title


def get_metadata(document_id):
    logger.info('get metadata url for document id: ' + str(document_id))
    xml_url = 'https://zoek.officielebekendmakingen.nl/' + document_id + '/metadata.xml'
    logger.info('get metadata url: ' + xml_url)
    page = requests.get(xml_url)
    tree = lxml.etree.fromstring(page.content)
    attributes_transtable = {
        'OVERHEIDop.dossiernummer': 'dossier_id',
        'DC.title': 'title_full',
        'OVERHEIDop.documenttitel': 'title_short',
        'OVERHEIDop.indiener': 'submitter',
        'OVERHEIDop.ondernummer': 'id_sub',
        'OVERHEIDop.publicationName': 'publication_type',
        'DCTERMS.issued': 'date_published',
        'OVERHEID.organisationType': 'organisation_type',
        'OVERHEID.category': 'category',
        'DC.creator': 'publisher'
    }

    metadata = {}
    for key, name in attributes_transtable.items():
        elements = tree.xpath('/metadata_gegevens/metadata[@name="' + key + '"]')
        if not elements:
            logger.warning('' + key + ' was not found')
            metadata[name] = ''
            continue
        if len(elements) > 1:
            # if name == 'category' or name == 'submitter':
            metadata[name] = ''
            for element in elements:
                if metadata[name]:
                    metadata[name] += '|'
                metadata[name] += element.get('content')
                logger.warning('more than 1 element found for key: ' + key + '!')
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

    return metadata


def search_politieknl_dossier(dossier_id):
    dossier_url = 'https://zoek.officielebekendmakingen.nl/dossier/' + str(dossier_id)
    page = requests.get(dossier_url)
    tree = lxml.html.fromstring(page.content)
    element = tree.xpath('//p[@class="info marge-onder"]/strong')
    n_publications = int(element[0].text)
    logger.info(str(n_publications) + ' results found')
    element = tree.xpath('//dl[@class="zoek-resulaten-info"]//dd')
    dossier_number = int(element[1].text)
    assert element[1].getprevious().text == 'Dossiernummer:'
    results = []
    pagnr = 1
    while len(results) < n_publications:
        logger.info('reading page: ' + str(pagnr))
        params = {
            '_page': pagnr,
            'sorttype': 1,
            'sortorder': 4,
        }
        pagnr += 1
        # print('request url: ' + dossier_url)
        page = requests.get(dossier_url, params)
        tree = lxml.html.fromstring(page.content)

        elements = tree.xpath('//div[@class="lijst"]/ul/li/a')
        for element in elements:
            title = element.text.strip().replace('\n', '')
            title = re.sub(r'\(.+?\)', '', title).strip()
            # print(title)
            result_info = element.find('em').text
            published_date = result_info.split('|')[0].strip()
            published_date = datetime.datetime.strptime(published_date, '%d-%m-%Y').date()
            # print(published_date)
            page_url = 'https://zoek.officielebekendmakingen.nl' + element.get('href')
            # print(page_url)
            type = result_info.split('|')[1].strip()
            publisher = result_info.split('|')[2].strip()

            result = {
                'title': title,
                'type': type,
                'publisher': publisher,
                'date_published': published_date,
                'page_url': page_url,
            }
            results.append(result)
    return results
