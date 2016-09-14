from django.test import TestCase

from website.create import create_or_update_dossier

from scraper import political_parties
from scraper import parliament_members


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
