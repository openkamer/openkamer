import re
from person.models import Person


def parse_name_surname_initials(name):
    name = remove_forename(name)
    name = name.replace(',', '')
    initials = find_initials(name)
    surname_prefix, pos = Person.find_prefix(name)
    surname = name.replace(surname_prefix, '').replace(initials, '').replace(',', '').strip()
    return initials, surname, surname_prefix


def remove_forename(name):
    # for members with the same surname, the forename is written behind the initials (example: Doe, B.A.(John))
    return re.sub(r"\(.*\)", "", name)


def find_initials(name):
    matches = re.search("(?:[A-Z]\.)+", name)
    if matches:
        return matches.group(0)
    else:
        return ''
