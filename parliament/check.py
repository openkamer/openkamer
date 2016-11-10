import datetime
import json
import logging
import os

logger = logging.getLogger(__name__)


def check_parliament_members_at_date(date):
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
            if start_date < date < end_date:
                members_active.append(member)
    return members_active
