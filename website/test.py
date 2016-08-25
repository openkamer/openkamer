from django.test import TestCase

from scraper.political_parties import create_parties

from website.create import create_or_update_dossier


class TestCreateDossier(TestCase):
    dossier_id = 33885

    def test_create_dossier(self):
        # TODO: tests takes a bit long, find smaller dossier or use mock objects
        create_parties()
        create_or_update_dossier(self.dossier_id)