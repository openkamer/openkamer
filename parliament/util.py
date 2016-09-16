import re


def parse_name_initials_surname(name):
    name = remove_forename(name)
    initials = name.split(' ')[0]
    surname = name.split('.')[-1].strip()
    return initials, surname


def parse_name_surname_initials(name):
    name = remove_forename(name)
    surname = name.split(',')[0]
    initials = name.split(',')[1].strip()
    return initials, surname


def remove_forename(name):
    # for members with the same surname, the forename is written behind the initials (example: Doe, B.A.(John))
    return re.sub(r"\(.*\)", "", name)