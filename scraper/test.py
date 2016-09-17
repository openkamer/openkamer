
import scraper.documents

metadata = scraper.documents.get_metadata(document_id='kst-29628-615')
#print(metadata)

metadata = scraper.documents.get_metadata(document_id='ag-tk-2015-09-18')
#metadata = scraper.documents.get_metadata(document_id='ag-ek-2015-11-19')

print(metadata)

# page_url = 'https://zoek.officielebekendmakingen.nl/kst-33885-7.html?zoekcriteria=%3fzkt%3dEenvoudig%26pst%3d%26vrt%3d33885%26zkd%3dInDeGeheleText%26dpr%3dAfgelopenDag%26spd%3d20160522%26epd%3d20160523%26sdt%3dDatumBrief%26ap%3d%26pnr%3d1%26rpp%3d10%26_page%3d4%26sorttype%3d1%26sortorder%3d4&resultIndex=34&sorttype=1&sortorder=4'
# scraper.documents.get_document_id(page_url)

# scraper.documents.search_politieknl_dossier(33885)