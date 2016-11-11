import datetime

from django.test import TestCase

from wikidata import wikidata

from parliament.models import Parliament

from parliament.util import parse_name_initials_surname
from parliament.util import parse_name_surname_initials



class TestParseName(TestCase):
    """ Tests name parsing """
    initials_expected = 'P.A.'
    surname_expected = 'Dijkstra'

    def check_result(self, initials, surname):
        self.assertEqual(initials, self.initials_expected)
        self.assertEqual(surname, self.surname_expected)

    def test_initials_surname(self):
        name = 'P.A. Dijkstra'
        initials, surname = parse_name_initials_surname(name)
        self.check_result(initials, surname)

    def test_initials_surname_forname(self):
        name = 'P.A. (Pia) Dijkstra'
        initials, surname = parse_name_initials_surname(name)
        self.check_result(initials, surname)
        name = 'P.A. (Pia)Dijkstra'
        initials, surname = parse_name_initials_surname(name)
        self.check_result(initials, surname)

    def test_surname_initials(self):
        name = 'Dijkstra, P.A.'
        initials, surname = parse_name_surname_initials(name)
        self.check_result(initials, surname)
        name = 'Dijkstra,P.A.'
        initials, surname = parse_name_surname_initials(name)
        self.check_result(initials, surname)

    def test_surname_initials_forname(self):
        name = 'Dijkstra, P.A.(Pia)'
        initials, surname = parse_name_surname_initials(name)
        self.check_result(initials, surname)
        name = 'Dijkstra, P.A. (Pia)'
        initials, surname = parse_name_surname_initials(name)
        self.check_result(initials, surname)
        name = 'Dijkstra,P.A.(Pia)'
        initials, surname = parse_name_surname_initials(name)
        self.check_result(initials, surname)


class TestPoliticalParty(TestCase):

    def test_get_political_party_memberships_wikidata(self):
        mark_rutte_wikidata_id = 'Q57792'
        item = wikidata.WikidataItem(mark_rutte_wikidata_id)
        parties = item.get_political_party_memberships()
        self.assertEqual(len(parties), 1)


class TestParliamentMembers(TestCase):
    fixtures = ['person.json', 'parliament.json']

    def test_get_members_at_date(self):
        tweede_kamer = Parliament.get_or_create_tweede_kamer()
        active_members = tweede_kamer.get_members_at_date(datetime.date(year=2016, month=6, day=1))
        print(len(active_members))  # TODO: check for number if members have non null joined/left fields
