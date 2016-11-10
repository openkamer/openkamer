import datetime
import json
import logging
import re

import requests
import lxml.html

from wikidata import wikidata

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


def search_members_wikidata():
    return wikidata.search_parliament_member_ids()


def search_members_check():
    # WARNING: this uses parliament member data from parlement.com, which has copyright
    url = 'http://www.parlement.com/id/vg7zoaah7lqb/selectiemenu_tweede_kamerleden?&u=%u2713&dlgid=k91ltodn5ambf&s01=k91ltod9pb6upd&v07=&v11=&v12=&v02=&v05=&v06=&Zoek=Ok&Reset=Reset'
    response = requests.get(url)
    tree = lxml.html.fromstring(response.content)
    rows = tree.xpath('//div[@class="seriekeuze seriekeuze_align"]')
    members = []
    for row in rows:
        name_line = row.xpath('ul/li[@class="plus"]/a')[0].text.strip()
        date_range_strings = [row.getnext().text]
        more_dates = row.getnext().xpath('br')
        for more_date in more_dates:
            date_range_strings.append(more_date.tail)
        extra_info = re.findall("\(.*?\)", name_line)
        name_line = re.sub("\(.*?\)", '', name_line).strip()
        name_line = re.sub("\s+", ' ', name_line)
        fractie = ''
        forename = ''
        if len(extra_info) >= 2:
            forename = remove_brackets(extra_info[0])
            fractie = remove_brackets(extra_info[1])
        elif len(extra_info) == 2:
            fractie = remove_brackets(extra_info[0])
        date_ranges = []
        for date_range_str in date_range_strings:
            fractie = remove_brackets(re.findall("\(.*?\)", date_range_str)[0])
            dates = re.findall("\d{4}-\d{2}-\d{2}", date_range_str)
            start_date = datetime.datetime.strptime(dates[0], '%Y-%m-%d').date()
            end_date = None
            if len(dates) == 2:
                end_date = datetime.datetime.strptime(dates[0], '%Y-%m-%d').date()
            date_ranges.append({
                'start_date': start_date,
                'end_date': end_date,
                'fractie': fractie,
            })
        initials = name_line.split(' ')[0]
        name = name_line.replace(initials, '').strip()
        member = {
            'name': name,
            'initials': initials,
            'forename': forename,
            'fractie': fractie,
            'date_ranges': date_ranges
        }
        # print('======================')
        # print(member)
        members.append(member)
    return members


def remove_brackets(text):
    return text.replace('(', '').replace(')', '')
