import requests
import lxml.html

from person.models import Person
from parliament.models import Parliament
from parliament.models import PoliticalParty
from parliament.models import PartyMember
from parliament.models import ParliamentMember


def create_members():
    url = 'http://www.tweedekamer.nl/kamerleden/alle_kamerleden'
    page = requests.get(url)
    tree = lxml.html.fromstring(page.content)

    parliament = get_or_create_tweede_kamer()

    rows = tree.xpath("//tbody/tr")

    for row in rows:
        columns = row.xpath("td")
        if len(columns) == 8:
            surname = columns[0][0].text.split(',')[0]
            print(surname)
            prefix = columns[0][0].text.split('.')[-1].strip()
            forename = columns[1][0].text
            if Person.person_exists(forename, surname):
                person = Person.objects.get(forename=forename, surname=surname)
            else:
                person = Person.objects.create(
                    forename=forename,
                    surname=surname,
                    surname_prefix=prefix,
                )
            party_name = columns[2][0].text
            party = PoliticalParty.get_or_create_party(party_name)
            # residence = columns[3][0].text
            # age = columns[4][0][0].text
            # sex = columns[5][0].text
            # assert age is not None
            # if sex == 'Man':
            #     sex = Member.MALE
            # elif sex == 'Vrouw':
            #     sex = Member.FEMALE
            party_member = PartyMember.objects.create(person=person, party=party)
            parliament_member = ParliamentMember.objects.create(person=person, parliament=parliament)
            print("new person: " + str(person))
            print("new party member: " + str(party_member))
            print("new parliament member: " + str(parliament_member))


def get_or_create_tweede_kamer():
    parliaments = Parliament.objects.filter(name='Tweede Kamer')
    if parliaments.exists():
        return parliaments[0]
    else:
        return Parliament.objects.create(name='Tweede Kamer', wikidata_id='Q233262')