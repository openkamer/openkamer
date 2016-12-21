import datetime
import logging
import re
import urllib.parse

import requests

logger = logging.getLogger(__name__)


def search(search_str, language='en'):
    search_url = 'https://www.wikidata.org/w/api.php'
    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'search': search_str,
        'language': language,
    }
    response = requests.get(search_url, params, timeout=60)
    return response.json()


def search_wikidata_id(search_str, language='en'):
    ids = search_wikidata_ids(search_str, language)
    if ids:
        return ids[0]
    return ''


def search_wikidata_ids(search_str, language='en'):
    results = search(search_str, language)
    ids = []
    if 'search' in results:
        for result in results['search']:
            ids.append(result['id'])
    return ids


def search_political_party_id(search_str, country_id='Q55', language='en'):
    wikidata_ids = search_wikidata_ids(search_str, language)
    wikidata_ids += search_wikidata_ids('Lid-' + search_str, language)
    possible_items = []
    for wikidata_id in wikidata_ids:
        item = WikidataItem(wikidata_id)
        if item.is_political_party():
            possible_items.append(item)
        elif item.is_fractie():
            possible_items.append(item)
    if len(possible_items) == 1:
        return possible_items[0].id
    for item in possible_items:
        if item.get_country_id() == country_id:
            return item.id
    return ''


def search_parliament_member_ids_with_start_date():
    logger.info('BEGIN')
    url = 'https://query.wikidata.org/sparql?'
    params = {
        'query': 'SELECT ?item WHERE { '
                 '?item wdt:P31 wd:Q5 . '
                 '?item p:P39 ?position_held_statement .'
                 '?position_held_statement ps:P39 wd:Q18887908 .'
                 '?position_held_statement pq:P580 ?start . '
                 '} ORDER BY DESC(?start)',
    ## taken from https://www.wikidata.org/wiki/User:Sjoerddebruin/Dutch_politics/Tweede_Kamer
        'format': 'json',
    }
    response = requests.get(url, params, timeout=60)
    response_json = response.json()
    member_ids = []
    for item in response_json['results']['bindings']:
        member_id = item['item']['value'].split('/')[-1]
        member_ids.append(member_id)
    logger.info('END')
    return set(member_ids)


def search_parliament_member_ids():
    logger.info('BEGIN')
    url = 'https://query.wikidata.org/sparql?'
    params = {
        'query': 'SELECT ?item WHERE { ?item wdt:P31 wd:Q5 . ?item wdt:P39 wd:Q18887908 . }',
    ## taken from https://www.wikidata.org/wiki/User:Sjoerddebruin/Dutch_politics/Tweede_Kamer
        'format': 'json',
    }
    response = requests.get(url, params, timeout=60)
    response_json = response.json()
    member_ids = []
    for item in response_json['results']['bindings']:
        member_id = item['item']['value'].split('/')[-1]
        member_ids.append(member_id)
    logger.info('END')
    return member_ids


class WikidataItem(object):

    def __init__(self, wikidata_id, language='nl'):
        self.id = wikidata_id
        site = 'wiki' + language
        self.item = self.get_item(wikidata_id, sites=site)

    @staticmethod
    def get_item(id, sites=None, props=None):
        assert id
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
        import time
        start = time.time()
        response = requests.get(url, params, timeout=60)
        logger.info(response.url)
        reponse_json = response.json()
        roundtrip = time.time() - start
        logger.info('response time: ' + str(roundtrip))
        item = reponse_json['entities'][id]
        return item

    def get_claims(self):
        return self.item['claims']

    def get_birth_date(self):
        claims = self.get_claims()
        if 'P569' in claims:  # date of birth
            birthdate = claims['P569'][0]['mainsnak']['datavalue']['value']['time']
            return WikidataItem.get_date(birthdate)
        return None

    def get_inception(self):
        claims = self.get_claims()
        if 'P571' in claims:
            inception = claims['P571'][0]['mainsnak']['datavalue']['value']['time']
            return WikidataItem.get_date(inception)
        return None

    def get_start_time(self):
        claims = self.get_claims()
        if 'P580' in claims:
            start_time = claims['P580'][0]['mainsnak']['datavalue']['value']['time']
            return WikidataItem.get_date(start_time)
        return None

    def get_end_time(self):
        claims = self.get_claims()
        if 'P582' in claims:
            end_time = claims['P582'][0]['mainsnak']['datavalue']['value']['time']
            return WikidataItem.get_date(end_time)
        return None

    def get_parts(self):
        claims = self.get_claims()
        if 'P527' in claims:
            return claims['P527']  # has part
        return None

    def get_country_id(self):
        claims = self.get_claims()
        if 'P17' in claims:
            return claims['P17'][0]['mainsnak']['datavalue']['value']['id']
        return None

    def is_political_party(self):
        claims = self.get_claims()
        if 'P31' in claims:
            for instance_of in claims['P31']:
                if instance_of['mainsnak']['datavalue']['value']['id'] == 'Q7278':
                    return True
        return False

    def get_given_names(self):
        claims = self.get_claims()
        if 'P735' in claims:
            given_names = []
            for value in claims['P735']:
                given_names.append(WikidataItem.get_label_for_id(value['mainsnak']['datavalue']['value']['id']))
            return given_names
        return ''

    def get_official_website(self):
        claims = self.get_claims()
        if 'P856' in claims:
            return claims['P856'][0]['mainsnak']['datavalue']['value']
        return ''

    def is_fractie(self):
        claims = self.get_claims()
        if 'P31' in claims:
            for instance_of in claims['P31']:
                if instance_of['mainsnak']['datavalue']['value']['id'] == 'Q848197':
                    return True
        return False

    def get_image_filename(self):
        claims = self.get_claims()
        if 'P18' in claims:
            return claims['P18'][0]['mainsnak']['datavalue']['value']
        return ''

    def get_logo_filename(self):
        claims = self.get_claims()
        if 'P154' in claims:
            return claims['P154'][0]['mainsnak']['datavalue']['value']
        return ''

    @staticmethod
    def get_label_for_id(id, language='en'):
        item = WikidataItem.get_item(id, props='labels')
        return WikidataItem.get_label_from_item(item, language=language)

    def get_label(self, language='en'):
        return WikidataItem.get_label_from_item(self.item, language=language)

    @staticmethod
    def get_label_from_item(item, language='en'):
        if 'labels' not in item or language not in item['labels']:
            return ''
        title = item['labels'][language]['value']
        return title

    def get_wikipedia_url(self, language='en'):
        site = language + 'wiki'
        if 'sitelinks' not in self.item or site not in self.item['sitelinks']:
            logger.info('wikipedia url not found for wikidata item: ' + str(self.id))
            return ''
        title = self.item['sitelinks'][site]['title']
        url = 'https://' + language + '.wikipedia.org/wiki/' + urllib.parse.quote(title)
        return url

    @staticmethod
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
        response = requests.get(url, params, timeout=60)
        response_json = response.json()
        pages = response_json['query']['pages']
        for page in pages.values():  #TODO: rewrite, does not loop
            wikimedia_image_url = page['imageinfo'][0]['thumburl']
            return wikimedia_image_url

    @staticmethod
    def get_date(date_str):
        try:
            date = datetime.datetime.strptime(date_str[1:11], '%Y-%m-%d')
            return date.date()
        except ValueError as error:
            result = re.findall("(\d{4})-00-00", date_str)
            if result:
                return datetime.date(year=int(result[0]), day=1, month=1)
            logger.error(error)
            return None

    def get_twitter_username(self):
        claims = self.get_claims()
        if 'P2002' in claims:
            return claims['P2002'][0]['mainsnak']['datavalue']['value']
        return ''

    def get_parlement_and_politiek_id(self):
        claims = self.get_claims()
        if 'P1749' in claims:
            return claims['P1749'][0]['mainsnak']['datavalue']['value']
        return ''

    def get_political_party_memberships(self):
        claims = self.get_claims()
        if 'P102' not in claims:
            return []
        memberships = []
        political_parties = claims['P102']
        # print(json.dumps(political_parties, sort_keys=True, indent=4))
        for party in political_parties:
            if not 'datavalue' in party['mainsnak']:
                logger.warning('datavalue not in party[\'mainsnak\'] for person with wikidata id: ' + str(id))
                continue
            member_info = {
                'wikidata_id': party['mainsnak']['datavalue']['value']['id'],
                'start_date': None,
                'end_date': None,
            }
            if 'qualifiers' in party and 'P580' in party['qualifiers']:
                start_time = party['qualifiers']['P580'][0]
                if 'datavalue' in start_time:
                    member_info['start_date'] = WikidataItem.get_date(start_time['datavalue']['value']['time'])
            if 'qualifiers' in party and 'P582' in party['qualifiers']:
                end_time = party['qualifiers']['P582'][0]
                if 'datavalue' in end_time:
                    member_info['end_date'] = WikidataItem.get_date(end_time['datavalue']['value']['time'])
            memberships.append(member_info)
        return memberships

    def get_positions_held(self, filter_position_id=None):
        claims = self.get_claims()
        if 'P39' not in claims:
            return []
        positions = []
        for pos in claims['P39']:
            # print(json.dumps(pos, sort_keys=True, indent=4))
            if not 'datavalue' in pos['mainsnak']:
                logger.warning('datavalue not in pos[\'mainsnak\'] for person with wikidata id: ' + str(id))
                continue
            position_id = pos['mainsnak']['datavalue']['value']['id']
            if filter_position_id and position_id != filter_position_id:
                continue
            start_time = None
            end_time = None
            if 'qualifiers' in pos and 'P580' in pos['qualifiers']:
                start_time = WikidataItem.get_date(pos['qualifiers']['P580'][0]['datavalue']['value']['time'])
                if len(pos['qualifiers']['P580']) > 1:
                    logger.warning('multiple start-times for a single position for wikidata_id: ' + str(id))
            if 'qualifiers' in pos and 'P582' in pos['qualifiers']:
                end_time = WikidataItem.get_date(pos['qualifiers']['P582'][0]['datavalue']['value']['time'])
                if len(pos['qualifiers']['P582']) > 1:
                    logger.warning('multiple end-times for a single position for wikidata_id: ' + str(id))
            position = {
                'id': position_id,
                # 'label': WikidataItem.get_label_for_id(position_id),
                'start_time': start_time,
                'end_time': end_time,
            }
            positions.append(position)
        return positions

    def get_parliament_positions_held(self):
        return self.get_positions_held(filter_position_id='Q18887908')
