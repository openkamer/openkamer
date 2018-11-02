import datetime
import json
import os
import re

from django.test import TestCase

import scraper.besluitenlijst
import scraper.documents
import scraper.dossiers
import scraper.parliament_members
import scraper.persons


class TestDossierScraper(TestCase):
    dossier_id = '33711'

    def test_scrape_dossier_url(self):
        dossier_url = scraper.dossiers.search_dossier_url(self.dossier_id)
        self.assertEqual(dossier_url, 'https://www.tweedekamer.nl/kamerstukken/wetsvoorstellen/detail?id=2013Z16228&dossier=33711')


class TestKamervraagScraper(TestCase):
    kamervraag_url = 'https://zoek.officielebekendmakingen.nl/kv-tk-2017Z06952'

    def test_get_kamervraag_id_and_content(self):
        kamervraag_html_url = self.kamervraag_url + '.html'
        document_id, content_html, title = scraper.documents.get_kamervraag_document_id_and_content(kamervraag_html_url)
        self.assertEqual(document_id, 'kv-tk-2017Z06952')
        self.assertEqual(len(content_html), 5990)
        self.assertEqual(title, 'Vragen van het lid Bosman (VVD) aan de Minister van Binnenlandse Zaken en Koninkrijksrelaties over het bericht «Ziekenhuis Curaçao bezorgt NL strop» (ingezonden 26 mei 2017).')
        overheidnl_document_ids = scraper.documents.get_kamervraag_antwoord_ids(self.kamervraag_url)
        self.assertEqual(len(overheidnl_document_ids), 1)
        self.assertEqual(overheidnl_document_ids[0], 'ah-tk-20162017-2167')

    def test_get_related_ids(self):
        url = 'https://zoek.officielebekendmakingen.nl/kv-tk-2017Z07318'
        related_document_ids = scraper.documents.get_kamervraag_antwoord_ids(url)
        self.assertEqual(len(related_document_ids), 2)
        self.assertEqual(related_document_ids[0], 'ah-tk-20162017-2129')
        self.assertEqual(related_document_ids[1], 'ah-tk-20162017-2338')


class TestBesluitenlijstScraper(TestCase):
    filenames = [
        'data/besluitenlijsten/besluitenlijst_example1.pdf',
        'data/besluitenlijsten/besluitenlijst_example2.pdf',
        'data/besluitenlijsten/besluitenlijst_example3.pdf',
        'data/besluitenlijsten/besluitenlijst_example4.pdf',
    ]

    @classmethod
    def setUpTestData(cls):
        cls.texts = []
        for filename in cls.filenames:
            text = scraper.besluitenlijst.besluitenlijst_pdf_to_text(filename)
            cls.texts.append(text)

    def test_regex(self):
        pattern = "\d{1,3}\.\s{0,}Agendapunt:"
        text = 'BuZa6.Agendapunt:Stukken'
        result = re.findall(pattern, text)
        self.assertEqual(result[0], '6.Agendapunt:')
        text = 'BuZa6.  Agendapunt:Stukken'
        result = re.findall(pattern, text)
        self.assertEqual(result[0], '6.  Agendapunt:')

    def test_find_agendapunten(self):
        for text in self.texts:
            items = scraper.besluitenlijst.find_agendapunten(text)
            self.assertTrue(len(items) > 0)

    def test_create_besluitenlijst(self):
        for text in self.texts:
            lijst = scraper.besluitenlijst.create_besluitenlijst(text)

    def test_find_cases(self):
        for text in self.texts:
            cases = scraper.besluitenlijst.find_cases(text)

    def test_find_case_decisions(self):
        for text in self.texts:
            punten = scraper.besluitenlijst.find_agendapunten(text)
            cases = scraper.besluitenlijst.find_cases(text)
            decisions = scraper.besluitenlijst.find_decisions(text)

    def test_create_besluit_items(self):
        for text in self.texts:
            items = scraper.besluitenlijst.create_besluit_items(text)


class TestPersonInfoScraper(TestCase):

    def test_inititals(self):
        parlement_and_politiek_id = 'vg09llk9rzrp'
        initials_expected = 'F.C.G.M.'
        initials = scraper.persons.get_initials(parlement_and_politiek_id)
        self.assertEqual(initials, initials_expected)
        parlement_and_politiek_id = 'vg09lll5uqzx'
        initials_expected = 'S.A.M.'
        initials = scraper.persons.get_initials(parlement_and_politiek_id)
        self.assertEqual(initials, initials_expected)
        parlement_and_politiek_id = 'vjuuhtscjwpn'
        initials_expected = 'T.H.P.'
        initials = scraper.persons.get_initials(parlement_and_politiek_id)
        self.assertEqual(initials, initials_expected)


class TestDocumentScraper(TestCase):

    def test_document_metadata_kamerstuk_2016(self):
        document_id = 'kst-34575-2'
        metadata = scraper.documents.get_metadata(document_id)
        self.assertEqual(metadata['publication_type'], 'Kamerstuk')
        self.assertEqual(metadata['dossier_id'], '34575')
        self.assertEqual(metadata['date_published'], '2016-10-13')
        self.assertEqual(metadata['title_short'], 'Voorstel van wet')
        self.assertEqual(metadata['title_full'], 'Wijziging van de Zorgverzekeringswet en de Wet op de zorgtoeslag in verband met enkele inhoudelijke en technische verbeteringen (Verzamelwet Zvw 2016); Voorstel van wet; Voorstel van wet')
        self.assertEqual(metadata['category'], 'Zorg en gezondheid | Ziekten en behandelingen')
        self.assertEqual(metadata['publisher'], 'Tweede Kamer der Staten-Generaal')
        self.assertEqual(metadata['submitter'], 'E.I. Schippers')
        self.assertEqual(metadata['publication_type'], 'Kamerstuk')

    def test_document_metadata_kamerstuk_2009(self):
        document_id = 'kst-32203-2'
        metadata = scraper.documents.get_metadata(document_id)
        self.assertEqual(metadata['publication_type'], 'Kamerstuk')
        self.assertEqual(metadata['dossier_id'], '32203')
        self.assertEqual(metadata['date_published'], '2009-11-06')
        self.assertEqual(metadata['title_short'], 'officiële publicatie')
        self.assertEqual(metadata['title_full'], 'Voorstel van Wet van de leden Van der Ham, De Wit en Teeven tot wijziging van het Wetboek van Strafrecht in verband met het laten vervallen van het verbod op godslastering; Voorstel van wet')
        self.assertEqual(metadata['category'], 'Recht | Strafrecht|Recht | Staatsrecht|Cultuur en recreatie | Cultuur')
        self.assertEqual(metadata['publisher'], 'Tweede Kamer der Staten-Generaal')
        self.assertEqual(metadata['submitter'], 'Ham van der B.|Wit de J.M.A.M.|Teeven F.')
        self.assertEqual(metadata['publication_type'], 'Kamerstuk')

    def test_get_document_content_2016(self):
        url = 'https://zoek.officielebekendmakingen.nl/kst-34575-2.html'
        document_id, content_html, title = scraper.documents.get_document_id_and_content(url)
        self.assertEqual(document_id, 'kst-34575-2')
        self.assertEqual(title, 'voorstel van wet')

    def test_get_document_content_2009(self):
        url = 'https://zoek.officielebekendmakingen.nl/kst-32203-2.html'
        document_id, content_html, title = scraper.documents.get_document_id_and_content(url)
        self.assertEqual(document_id, 'kst-32203-2')
        self.assertEqual(title, 'voorstel van wet')
        url = 'https://zoek.officielebekendmakingen.nl/kst-31830-6.html'
        document_id, content_html, title = scraper.documents.get_document_id_and_content(url)
        self.assertEqual(document_id, 'kst-31830-6')
        self.assertEqual(title, 'brief van de minister van financiën')
