from datetime import datetime
import re

import requests
import lxml
import lxml.html
import lxml.etree


def get_document_id_and_content(url):
    print('get document id for url: ' + url)
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
    print('document id: ' + document_id)
    elements = tree.xpath('//div[@class="stuk"]')
    if elements:
        content_html = lxml.etree.tostring(elements[0])
    else:
        content_html = ''
    return document_id, content_html


def get_metadata(document_id):
    print('get metadata url for document id: ' + str(document_id))
    xml_url = 'https://zoek.officielebekendmakingen.nl/' + document_id + '/metadata.xml'
    print('get metadata url: ' + xml_url)
    page = requests.get(xml_url)
    print('server responded')
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
            print('WARNING: ' + key + ' was not found')
            metadata[name] = ''
            continue
        if len(elements) > 1:
            if name == 'category':
                metadata[name] = ''
                for element in elements:
                    if metadata[name]:
                        metadata[name] += ' | '
                    metadata[name] += element.get('content')
            else:
                print('WARNING: more than 1 element found for key: ' + key + ', using first, but more info available!')
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

    return metadata


def search_politieknl_dossier(dossier_id):
    dossier_url = 'https://zoek.officielebekendmakingen.nl/dossier/' + str(dossier_id)

    page = requests.get(dossier_url)
    tree = lxml.html.fromstring(page.content)
    element = tree.xpath('//p[@class="info marge-onder"]/strong')
    n_publications = int(element[0].text)
    print(str(n_publications) + ' results found')
    element = tree.xpath('//dl[@class ="zoek-resulaten-info"]//dd')
    dossier_number = int(element[1].text)
    assert element[1].getprevious().text == 'Dossiernummer:'
    print(dossier_number)

    results = []
    pagnr = 1
    while len(results) < n_publications:
        print('reading page: '  + str(pagnr))
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
            published_date = datetime.strptime(published_date, '%d-%m-%Y').date()
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

        print('------')
        print(result['type'])
        print(result['title'])
        print(result['date_published'])
        print(result['publisher'])
        print(result['page_url'])
    return results
