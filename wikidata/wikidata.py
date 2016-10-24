from datetime import datetime
import json
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


def get_label(id, language='en'):
    item = get_item(id, props='labels')
    if not 'labels' in item:
        return ''
    title = item['labels'][language]['value']
    return title


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


def get_given_name(id):
    claims = get_claims(id)
    if 'P735' in claims:
        return get_label(claims['P735'][0]['mainsnak']['datavalue']['value']['id'])
    return ''


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
    for page in pages.values():  #TODO: rewrite, does not loop
        wikimedia_image_url = page['imageinfo'][0]['thumburl']
        return wikimedia_image_url


def get_birth_date(id):
    claims = get_claims(id)
    if 'P569' in claims:  # date of birth
        birthdate = claims['P569'][0]['mainsnak']['datavalue']['value']['time']
        return get_date(birthdate)
    return None


def get_inception(id):
    claims = get_claims(id)
    if 'P571' in claims:
        inception = claims['P571'][0]['mainsnak']['datavalue']['value']['time']
        return get_date(inception)
    return None


def get_start_time(id):
    claims = get_claims(id)
    if 'P580' in claims:
        start_time = claims['P580'][0]['mainsnak']['datavalue']['value']['time']
        return get_date(start_time)
    return None


def get_end_time(id):
    claims = get_claims(id)
    if 'P582' in claims:
        end_time = claims['P582'][0]['mainsnak']['datavalue']['value']['time']
        return get_date(end_time)
    return None


def get_parts(id):
    claims = get_claims(id)
    if 'P527' in claims:
        return claims['P527']  # has part
    return None


def get_date(date_str):
    try:
        date = datetime.strptime(date_str[1:11], '%Y-%m-%d')
        return date.date()
    except ValueError as error:
        print(error)
        return None


def get_parlement_and_politiek_id(id):
    claims = get_claims(id)
    if 'P1749' in claims:
        return claims['P1749'][0]['mainsnak']['datavalue']['value']
    return ''


def get_political_party_memberships(id):
    claims = get_claims(id)
    if 'P102' not in claims:
        return []
    memberships = []
    political_parties = claims['P102']
    # print(json.dumps(political_parties, sort_keys=True, indent=4))
    for party in political_parties:
        member_info = {'wikidata_id': party['mainsnak']['datavalue']['value']['id']}
        member_info['start_date'] = None
        member_info['end_date'] = None
        if 'qualifiers' in party and 'P580' in party['qualifiers']:
            member_info['start_date'] = get_date(party['qualifiers']['P580'][0]['datavalue']['value']['time'])
        if 'qualifiers' in party and 'P582' in party['qualifiers']:
            member_info['end_date'] = get_date(party['qualifiers']['P582'][0]['datavalue']['value']['time'])
        memberships.append(member_info)
    return memberships
