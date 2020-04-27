import json
import logging
from typing import List

from wikidata import wikidata

logger = logging.getLogger(__name__)


class GovernmentMemberData:
    def __init__(self):
        self.position_name = ''
        self.position = None
        self.properties = []
        self.wikidata_id = None
        self.wikipedia_url = None
        self.name = None
        self.parlement_and_politiek_id = None
        self.ministry = None
        self.start_date = None
        self.end_date = None


def get_government_members(government_wikidata_id, max_members=None) -> List[GovernmentMemberData]:
    logger.info('BEGIN')
    language = 'nl'
    parts = wikidata.WikidataItem(government_wikidata_id).get_parts()
    members = []
    for part in parts:
        member = GovernmentMemberData()
        member.wikidata_id = part['mainsnak']['datavalue']['value']['id']
        member_item = wikidata.WikidataItem(member.wikidata_id)
        member.wikipedia_url = member_item.get_wikipedia_url(language=language)
        member.name = member_item.get_label(language=language)
        member.parlement_and_politiek_id = member_item.get_parlement_and_politiek_id()
        for prop_id in part['qualifiers']:
            prop = part['qualifiers'][prop_id][0]
            # print(json.dumps(prop, sort_keys=True, indent=4))
            if prop['datatype'] == 'wikibase-item':
                item_id = prop['datavalue']['value']['id']
                item_label = wikidata.WikidataItem(item_id).get_label(language=language)
                item_label = item_label.lower()
                member.properties.append(item_label)
                if 'ministerie' in item_label:
                    member.ministry = item_label.replace('ministerie van', '').strip()
                elif 'minister voor' in item_label or 'minister van' in item_label:
                    member.position_name = item_label.replace('minister voor', '').replace('minister van', '').strip()
                elif member.position is None:
                    if 'viceminister' in item_label or 'vicepremier' in item_label:
                        member.position = 'viceminister-president'
                    elif 'minister-president' in item_label or 'premier' in item_label:
                        member.position = 'minister-president'
                    elif 'staatssecretaris' in item_label:
                        member.position = 'staatssecretaris'
                    elif 'minister zonder portefeuille' in item_label:
                        member.position = 'minister zonder portefeuille'
                    elif 'minister' in item_label:
                        member.position = 'minister'
            if prop['property'] == 'P580':  # start time
                member.start_date = wikidata.WikidataItem.get_date(prop['datavalue']['value']['time'])
            if prop['property'] == 'P582':  # end time
                member.end_date = wikidata.WikidataItem.get_date(prop['datavalue']['value']['time'])
        logger.info(json.dumps(member.__dict__, sort_keys=True, default=str))
        members.append(member)
        if max_members and  len(members) >= max_members:
            break
    logger.info('END')
    return members


def get_government(government_wikidata_id):
    item = wikidata.WikidataItem(government_wikidata_id)
    return {
        'name': item.get_label(language='nl'),
        'start_date': item.get_start_time(),
        'end_date': item.get_end_time(),
    }
