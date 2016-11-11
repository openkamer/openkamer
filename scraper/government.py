import json
import logging

from wikidata import wikidata

logger = logging.getLogger(__name__)


def get_government(government_wikidata_id):
    item = wikidata.WikidataItem(government_wikidata_id)
    return {
        'name': item.get_label(language='nl'),
        'start_date': item.get_start_time(),
        'end_date': item.get_end_time(),
    }


def get_government_members(government_wikidata_id, max_members=None):
    logger.info('BEGIN')
    parts = wikidata.WikidataItem(government_wikidata_id).get_parts()
    members = []
    for part in parts:
        member = {}
        member['position_name'] = ''  # used for ministers without portfolio
        member['properties'] = []
        member['wikidata_id'] = part['mainsnak']['datavalue']['value']['id']
        member['wikipedia_url'] = wikidata.WikidataItem.get_wikipedia_url(member['wikidata_id'], language='nl')
        member_item = wikidata.WikidataItem(member['wikidata_id'])
        member['name'] = member_item.get_label(language='nl')
        member['parlement_and_politiek_id'] = member_item.get_parlement_and_politiek_id()
        for prop_id in part['qualifiers']:
            prop = part['qualifiers'][prop_id][0]
            # print(json.dumps(prop, sort_keys=True, indent=4))
            if prop['datatype'] == 'wikibase-item':
                item_id = prop['datavalue']['value']['id']
                # print(item_id)
                item_label = wikidata.WikidataItem(item_id).get_label(language='nl')
                item_label = item_label.lower()
                member['properties'].append(item_label)
                if 'ministerie' in item_label:
                    member['ministry'] = item_label.replace('ministerie van', '').strip()
                elif 'minister voor' in item_label:
                    member['position_name'] = item_label.replace('minister voor', '').strip()
                elif 'position' not in member:
                    if 'viceminister' in item_label or 'vicepremier' in item_label:
                        member['position'] = 'viceminister-president'
                    elif 'minister-president' in item_label or 'premier' in item_label:
                        member['position'] = 'minister-president'
                    elif 'staatssecretaris' in item_label:
                        member['position'] = 'staatssecretaris'
                    elif 'minister zonder portefeuille' in item_label:
                        member['position'] = 'minister zonder portefeuille'
                    elif 'minister' in item_label:
                        member['position'] = 'minister'
            if prop['property'] == 'P580':  # start time
                member['start_date'] = wikidata.WikidataItem.get_date(prop['datavalue']['value']['time'])
            if prop['property'] == 'P582':  # end time
                member['end_date'] = wikidata.WikidataItem.get_date(prop['datavalue']['value']['time'])
        logger.info(member)
        members.append(member)
        if max_members and  len(members) >= max_members:
            break
    logger.info('END')
    return members
