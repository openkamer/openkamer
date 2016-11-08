import requests
import logging

import lxml.html

logger = logging.getLogger(__name__)


def search_members():
    url = 'http://www.tweedekamer.nl/kamerleden/alle_kamerleden'
    page = requests.get(url)
    tree = lxml.html.fromstring(page.content)
    rows = tree.xpath("//tbody/tr")
    members = []
    for row in rows:
        columns = row.xpath("td")
        if len(columns) == 8:
            forename = columns[1][0].text
            surname = columns[0][0].text.split(',')[0]
            prefix = columns[0][0].text.split('.')[-1].strip()
            initials = columns[0][0].text.split(',')[1].replace(prefix, '').replace(' ', '')
            party = columns[2][0].text
            member = {
                'forename': forename,
                'surname': surname,
                'prefix': prefix,
                'initials': initials,
                'party': party
            }
            members.append(member)
    return members


def create_members_csv(members, filepath):
    with open(filepath, 'w') as fileout:
        fileout.write('forename,surname,name prefix,initials,party\n')
        for member in members:
            fileout.write(member['forename'] + ',' + member['surname'] + ',' + member['prefix'] + ',' + member['initials'] + ',' + member['party'] + '\n')
