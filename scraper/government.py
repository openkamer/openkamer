import json

from wikidata import wikidata


def get_government(government_wikidata_id):
    return wikidata.get_claims(id=government_wikidata_id)


def get_government_members(government_wikidata_id):
    parts = wikidata.get_parts(government_wikidata_id)
    for part in parts:
        member = {}
        member['properties'] = []
        member['wikidata_id'] = part['mainsnak']['datavalue']['value']['id']
        member['wikipedia_url'] = wikidata.get_wikipedia_url(member['wikidata_id'], language='nl')
        member['name'] = wikidata.get_item(member['wikidata_id'])['labels']['nl']['value']
        for prop_id in part['qualifiers']:
            prop = part['qualifiers'][prop_id][0]
            # print(json.dumps(prop, sort_keys=True, indent=4))
            if prop['datatype'] == 'wikibase-item':
                item_id = prop['datavalue']['value']['id']
                # print(item_id)
                item_label = wikidata.get_label(item_id, language='nl')
                member['properties'].append(item_label)
                if 'ministerie' in item_label.lower():
                    member['ministry'] = item_label.lower().replace('ministerie van', '').strip()
                elif 'minister voor' in item_label.lower():
                    member['ministry'] = item_label.lower().replace('minister voor', '').strip()
                if 'minister-president' in item_label.lower():
                    member['position'] = 'minister-president'
                elif 'viceminister' in item_label.lower():
                    member['position'] = 'viceminister-president'
                elif 'staatssecretaris' in item_label.lower():
                    member['position'] = 'staatssecretaris'
                elif 'minister' in item_label.lower():
                    member['position'] = 'minister'
            if prop['property'] == 'P580':  # start time
                member['start_date'] = wikidata.get_date(prop['datavalue']['value']['time'])
                # print(member['start_date'])
            if prop['property'] == 'P582':  # end time
                member['end_date'] = wikidata.get_date(prop['datavalue']['value']['time'])
                # print(member['end_date'])
        print('=======================================')
        print(member)
        # print(json.dumps(member_properties, sort_keys=True, indent=4))
