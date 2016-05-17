import re

import requests
import lxml.html

from parliament.models import PoliticalParty


def create_parties():
    url = 'https://www.tweedekamer.nl/kamerleden/fracties'
    page = requests.get(url)
    tree = lxml.html.fromstring(page.content)

    rows = tree.xpath("//ul[@class='reset grouped-list']/li/a")
    for row in rows:
        columns = row.text.split('-')
        if len(columns) > 1:
            name = columns[0].strip()
            name_short = columns[1]
            name_short = re.sub(r'\(.+?\)', '', name_short).strip()
        else:
            name = columns[0]
            name = re.sub(r'\(.+?\)', '', name).strip()
            name_short = name
        # print('name: ' + name)
        # print('short: ' + name_short)
        if PoliticalParty.find_party(name):
            print('WARNING: party already exists!')
        else:
            party = PoliticalParty.objects.create(name=name, name_short=name_short)
            party.update_info('nl', 'nl')
            party.save()
            print('created: ' + str(party))
