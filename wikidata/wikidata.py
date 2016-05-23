from datetime import datetime
import urllib.parse

import requests


def search(search_str, language='en'):
    search_url = 'https://www.wikidata.org/w/api.php'
    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'search': search_str,
        'language': language,
    }
    response = requests.get(search_url, params)
    return response.json()


def search_wikidata_id(search_str, language='en'):
    ids = search_wikidata_ids(search_str, language)
    if ids:
        return ids[0]
    return None


def search_wikidata_ids(search_str, language='en'):
    results = search(search_str, language)
    ids = []
    if 'search' in results:
        for result in results['search']:
            ids.append(result['id'])
    return ids


def get_item(id, sites=None, props=None):
    url = 'https://www.wikidata.org/w/api.php'
    params = {
        'action': 'wbgetentities',
        'ids': id,
        'format': 'json'
    }
    if sites:
        params['sites'] = sites
    if props:
        params['props'] = props
    response = requests.get(url, params)
    reponse_json = response.json()
    item_json = reponse_json['entities'][id]
    return item_json


def get_claims(id):
    item = get_item(id)
    return item['claims']


def get_wikipedia_url(id, language='en'):
    site = language + 'wiki'
    item = get_item(id, sites=site, props='sitelinks')
    if not 'sitelinks' in item:
        return ''
    if not site in item['sitelinks']:
        return ''
    title = item['sitelinks'][site]['title']
    url = 'https://' + language + '.wikipedia.org/wiki/' + urllib.parse.quote(title) + ''
    return url


def get_country_id(id):
    claims = get_claims(id)
    if 'P17' in claims:
        return claims['P17'][0]['mainsnak']['datavalue']['value']['numeric-id']
    return None


def get_official_website(id):
    claims = get_claims(id)
    if 'P856' in claims:
        return claims['P856'][0]['mainsnak']['datavalue']['value']
    return None


def get_image_filename(id):
    claims = get_claims(id)
    if 'P18' in claims:
        return claims['P18'][0]['mainsnak']['datavalue']['value']
    return None


def get_logo_filename(id):
    claims = get_claims(id)
    if 'P154' in claims:
        return claims['P154'][0]['mainsnak']['datavalue']['value']
    return None


def get_wikimedia_image_url(filename, image_width_px=220):
    url = 'https://commons.wikimedia.org/w/api.php'
    params = {
        'action': 'query',
        'titles': 'File:' + filename,
        'prop': 'imageinfo',
        'iiprop': 'url',
        'iiurlwidth': str(image_width_px),
        'format': 'json',
    }
    response = requests.get(url, params)
    response_json = response.json()
    pages = response_json['query']['pages']
    for page in pages.values():
        wikimedia_image_url = page['imageinfo'][0]['thumburl']
        return wikimedia_image_url


def get_birth_date(id):
    claims = get_claims(id)
    if 'P569' in claims:  # date of birth
        birthdate = claims['P569'][0]['mainsnak']['datavalue']['value']['time']
        try:
            birthdate = datetime.strptime(birthdate[1:11], '%Y-%m-%d')
            return birthdate.date()
        except ValueError as error:
            print(error)
            return None
    return None


def get_inception(id):
    claims = get_claims(id)
    if 'P571' in claims:
        inception = claims['P571'][0]['mainsnak']['datavalue']['value']['time']
        try:
            inception = datetime.strptime(inception[1:11], '%Y-%m-%d')
            return inception.date()
        except ValueError as error:
            print(error)
            return None
    return None