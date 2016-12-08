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
    page = requests.get(url, timeout=60)
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


def search_members_wikidata(all_members=False):
    if all_members:
        return wikidata.search_parliament_member_ids()
    else:
        return wikidata.search_parliament_member_ids_with_start_date()


def search_members_check():
    # WARNING: this uses parliament member data from parlement.com, which has copyright
    url = ''  # This url becomes invalid after time, goto http://www.parlement.com/id/vg7zoaah7lqb/selectiemenu_tweede_kamerleden and create a new one
    if not url:
        logger.error('please set a valid url')
    response = requests.get(url, timeout=60)
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
        name_line = re.sub("\(.*\)", '', name_line).strip()
        name_line = re.sub("\s+", ' ', name_line)
        forename = ''
        if len(extra_info) >= 2:
            forename = remove_brackets(extra_info[0])
        date_ranges = []
        for date_range_str in date_range_strings:
            fractie = remove_brackets(re.findall("\(.*?\)", date_range_str)[0])
            dates = re.findall("\d{4}-\d{2}-\d{2}", date_range_str)
            start_date = datetime.datetime.strptime(dates[0], '%Y-%m-%d').date()
            end_date = ''
            if len(dates) == 2:
                end_date = datetime.datetime.strptime(dates[1], '%Y-%m-%d').date() + datetime.timedelta(days=1)
            date_ranges.append({
                'start_date': start_date,
                'end_date': end_date,
                'fractie': fractie,
            })
        initials = name_line.split(' ')[0]
        name = name_line.replace(initials, '')
        name = name.replace('MPM', '')  # Fred Teeven has this surfix that should not be there
        name = name.strip()
        member = {
            'name': name,
            'initials': initials,
            'forename': forename,
            'date_ranges': date_ranges
        }
        # print('======================')
        # print(member)
        members.append(member)
    return members


def search_members_check_json():
    members = search_members_check()
    return json.dumps(members, sort_keys=True, indent=4, ensure_ascii=False, default=json_serial)


def remove_brackets(text):
    return text.replace('(', '').replace(')', '')


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime.date):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")