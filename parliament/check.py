import datetime
import json
import logging
import os

from unidecode import unidecode

logger = logging.getLogger(__name__)


def check_parliament_members_at_date(check_date):
    filepath = './data/secret/parliament_members_check.json'
    if not os.path.exists(filepath):
        logger.error('file ' + filepath + ' does note exist!')
        return []
    with open(filepath, 'r') as filein:
        members_json = json.loads(filein.read())
    members_active = []
    for member in members_json:
        for date_range in member['date_ranges']:
            start_date = datetime.datetime.strptime(date_range['start_date'], "%Y-%m-%d").date()
            if date_range['end_date'] != '':
                end_date = datetime.datetime.strptime(date_range['end_date'], "%Y-%m-%d").date()
            else:
                end_date = datetime.date.today() + datetime.timedelta(days=1)
            # print(str(start_date) + ' - ' + str(end_date) + ' [' + str(check_date) + ']')
            if start_date < check_date < end_date:
                members_active.append(member)
    return members_active


def get_members_missing(members_current, members_current_check):
    members_missing = []
    for member_check in members_current_check:
        found = False
        member_check_name = unidecode(member_check['name'])
        member_check_forename = unidecode(member_check['forename'])
        for member in members_current:
            member_name = unidecode(member.person.surname_including_prefix())
            if member_check_name == member_name and member_check_forename == unidecode(member.person.forename):
                found = True
                break
        if not found:
            members_missing.append(
                member_check['initials'] + ' ' + member_check['name'] + ' (' + member_check['forename'] + ')')
            # print(member_check['name'])
    return members_missing


def get_members_incorrect(members_current, members_current_check):
    members_incorrect = []
    for member in members_current:
        found = False
        member_name = unidecode(member.person.surname_including_prefix())
        member_forename = unidecode(member.person.forename)
        for member_check in members_current_check:
            member_check_name = unidecode(member_check['name'])
            member_check_forename = unidecode(member_check['forename'])
            if member_check_name == member_name and member_check_forename == member_forename:
                found = True
                break
        if not found:
            members_incorrect.append(member)
            # print(member.person.fullname())
    return members_incorrect
