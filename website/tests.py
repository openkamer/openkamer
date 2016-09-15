from django.test import TestCase

from scraper import political_parties
from scraper import parliament_members

from parliament.models import ParliamentMember

from website.create import create_or_update_dossier


class TestCreateParliament(TestCase):

    def test_create_parliament(self):
        political_parties.create_parties()
        parliament_members.create_members()


class TestCreateDossier(TestCase):
    fixtures = ['parliament_2016.json']

    def test_create_dossier_33885(self):
        create_or_update_dossier(33885)

    def test_create_dossier_33506(self):
        create_or_update_dossier(33506)


class TestFindParliamentMembers(TestCase):
    fixtures = ['parliament_2016.json']

    def test_find_member(self):
        surname = 'Zijlstra'
        forename = 'Halbe'
        initials = 'H.'
        member = ParliamentMember.find(surname=surname, initials=initials)
        self.assertEqual(member.person.forename, forename)

    def test_find_member_surname_prefix(self):
        surname = 'Weyenberg van'
        forename = 'Steven'
        initials = 'S.P.R.A.'
        member = ParliamentMember.find(surname=surname, initials=initials)
        self.assertEqual(member.person.forename, forename)
        surname = 'van Weyenberg'
        member = ParliamentMember.find(surname=surname, initials=initials)
        self.assertEqual(member.person.forename, forename)

    def test_find_member_non_ascii(self):
        surname = 'Koser Kaya'
        forename = 'Fatma'
        initials = 'F.'
        member = ParliamentMember.find(surname=surname, initials=initials)
        self.assertEqual(member.person.forename, forename)
