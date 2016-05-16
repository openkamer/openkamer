import wikidata


results = wikidata.search('PvdA')
# print(results)

wikidata_id = wikidata.search_wikidata_id('PvdA')
print(wikidata_id)

item = wikidata.get_item(wikidata_id)
# print(item)

image_name = wikidata.get_image_filename(wikidata_id)
print(image_name)

logo_name = wikidata.get_logo_filename(wikidata_id)
print(logo_name)