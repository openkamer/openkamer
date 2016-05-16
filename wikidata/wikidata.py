from datetime import datetime

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
    results = search(search_str, language)
    if not results['search']:
        print('no wikidata found for ' + search_str)
        return None
    wikidata_id = results['search'][0]['id']
    return wikidata_id


def get_item(id):
    url = 'https://www.wikidata.org/wiki/Special:EntityData/' + id
    params = {'format': 'json'}
    response = requests.get(url, params)
    reponse_json = response.json()
    item_json = reponse_json['entities'][id]
    return item_json


def get_claims(id):
    item = get_item(id)
    return item['claims']


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