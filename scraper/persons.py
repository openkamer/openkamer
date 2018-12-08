import logging

import requests
import lxml.html

logger = logging.getLogger(__name__)

TITLES = (
    'dr.',
    'mr.',
    'ir.',
    'drs.',
    'bacc.',
    'kand.',
    'prof.',
    'ds.',
    'ing.',
    'bc.',
    'BA.',
    'BSc.',
    'LBB.',
    'LLM.',
    'MA.',
    'MSc.',
    'MPhil.',
    'PhD.',
)


def get_initials(parlement_and_politiek_id):
    if not parlement_and_politiek_id:
        return ''
    url = 'https://www.parlement.com/id/' + parlement_and_politiek_id + '/'
    page = requests.get(url, timeout=60)
    tree = lxml.html.fromstring(page.content)
    title = tree.xpath("//title")[0].text
    name_parts = title.split(' ')  # this includes the title, if applicable, for example: Ir. J.R.V.A. (Jeroen) Dijsselbloem
    initials = name_parts[0]
    for title in TITLES:
        if title.lower() in name_parts[0].lower():
            initials = name_parts[1]
    initials = clean_initials(initials)
    return initials


def clean_initials(initials):
    """ Removes the second character in initials, for example: 'Th.H.Ph.' is changed to 'T.H.P.' """
    parts = initials.split('.')
    initials_new = ''
    for part in parts:
        if not part:
            continue
        initials_new += part[0] + '.'
    return initials_new
