from datetime import datetime
import re

import requests
import lxml.html
import lxml


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
            short_title = result_info.split('|')[1].strip()
            publisher = result_info.split('|')[2].strip()

            result = {
                'title': title,
                'short_title': short_title,
                'publisher': publisher,
                'published_date': published_date,
                'page_url': page_url,
            }
            results.append(result)

        print('------')
        print(result['short_title'])
        print(result['title'])
        print(result['published_date'])
        print(result['publisher'])
        print(result['page_url'])
    return results