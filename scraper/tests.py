import json
import datetime
import re

from django.test import TestCase

from wikidata import wikidata

import scraper.documents
import scraper.votings
import scraper.government
import scraper.persons
import scraper.besluitenlijst

# metadata = scraper.documents.get_metadata(document_id='kst-33885-7')
# print(metadata)

# page_url = 'https://zoek.officielebekendmakingen.nl/kst-33885-7.html?zoekcriteria=%3fzkt%3dEenvoudig%26pst%3d%26vrt%3d33885%26zkd%3dInDeGeheleText%26dpr%3dAfgelopenDag%26spd%3d20160522%26epd%3d20160523%26sdt%3dDatumBrief%26ap%3d%26pnr%3d1%26rpp%3d10%26_page%3d4%26sorttype%3d1%26sortorder%3d4&resultIndex=34&sorttype=1&sortorder=4'
# scraper.documents.get_document_id(page_url)

# scraper.documents.search_politieknl_dossier(33885)


class TestVoortouwCommissieScraper(TestCase):

    def test_get_commissies(self):
        commissions = scraper.besluitenlijst.get_voortouwcommissies_besluiten_urls()
        self.assertTrue(len(commissions) >= 37)

    def test_get_besluitenlijst_urls(self):
        overview_url = 'https://www.tweedekamer.nl/kamerstukken/besluitenlijsten?qry=%2A&fld_tk_categorie=Kamerstukken&srt=date%3Adesc%3Adate&clusterName=Besluitenlijsten&Type=Kamerstukken&fld_prl_kamerstuk=Besluitenlijsten&nocache=&fld_prl_voortouwcommissie=Vaste+commissie+voor+binnenlandse+zaken'
        urls = scraper.besluitenlijst.get_besluitenlijsten_urls(overview_url, max_results=10)
        self.assertEqual(len(urls), 10)


class TestBesluitenlijstScraper(TestCase):
    filenames = [
        # 'data/besluitenlijsten/besluitenlijst_example1.pdf',
        # 'data/besluitenlijsten/besluitenlijst_example2.pdf',
        # 'data/besluitenlijsten/besluitenlijst_example3.pdf',
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


class TestGovernmentScraper(TestCase):
    rutte_2_wikidata_id = 'Q1638648'

    def test(self):
        government = scraper.government.get_government(self.rutte_2_wikidata_id)
        self.assertEqual(government['name'], 'Kabinet-Rutte II')
        self.assertEqual(government['start_date'], datetime.date(2012, 11, 5))

    def test_get_members(self):
        members = scraper.government.get_government_members(self.rutte_2_wikidata_id)

    def test_get_parlement_and_politiek_id(self):
        person_wikidata_id = 'Q32681'
        expected_id = 'vg09llk9rzrp'
        parlement_id = wikidata.get_parlement_and_politiek_id(person_wikidata_id)
        self.assertEqual(parlement_id, expected_id)


class TestWetsvoorstellenDossierScraper(TestCase):
    max_results = 40

    def test_get_initiatief_wetsvoorstellen_dossier_ids(self):
        dossier_ids = scraper.documents.get_dossier_ids_wetsvoorstellen_initiatief(max_results=self.max_results)
        # print('initiatief wetsvoorstel dossiers found: ' + str(len(dossier_ids)))
        # with open('data/dossier_ids_wetsvoorstellen_initiatief.txt', 'w') as fileout:
        #     for dossier_id in dossier_ids:
        #         fileout.write(dossier_id + '\n')
        self.assertEqual(len(dossier_ids), self.max_results)

    def test_get_regering_wetsvoorstellen_dossier_ids(self):
        dossier_ids = scraper.documents.get_dossier_ids_wetsvoorstellen_regering(max_results=self.max_results)
        # print('regering wetsvoorstel dossiers found: ' + str(len(dossier_ids)))
        # with open('data/dossier_ids_wetsvoorstellen_regering.txt', 'w') as fileout:
        #     for dossier_id in dossier_ids:
        #         fileout.write(dossier_id + '\n')
        self.assertEqual(len(dossier_ids), self.max_results)


class TestVotingScraper(TestCase):
    dossier_nr_party_votes = 33885
    dossier_nr_individual_votes = 33506

    def test_get_voting_pages_for_dossier(self):
        expected_urls = [
            'https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2016P10154',
            'https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2016P10153'
        ]
        votings_urls = scraper.votings.get_voting_pages_for_dossier(self.dossier_nr_party_votes)
        self.assertEqual(len(expected_urls), len(votings_urls))
        for i in range(len(votings_urls)):
            # print(votings_urls[i])
            self.assertEqual(votings_urls[i], expected_urls[i])

    def test_get_votings_for_page(self):
        voting_page_urls = [
            'https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2016P10154',
            'https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2016P10153'
        ]
        expected_results = [
            {'result': 'Verworpen', 'document_id': '33885-17'},
            {'result': 'Aangenomen', 'document_id': '33885-30'},
            {'result': 'Verworpen', 'document_id': '33885-19'},
            {'result': 'Verworpen', 'document_id': '33885-20'},
            {'result': 'Eerder ingetrokken (tijdens debat)', 'document_id': '33885-21'},
            {'result': 'Verworpen', 'document_id': '33885-31'},
            {'result': 'Aangehouden (tijdens debat)', 'document_id': '33885-23'},
            {'result': 'Verworpen', 'document_id': '33885-24'},
            {'result': 'Aangehouden (tijdens debat)', 'document_id': '33885-25'},
            {'result': 'Verworpen', 'document_id': '33885-26'},
            {'result': 'Verworpen', 'document_id': '33885-27'},
            {'result': 'Eerder ingetrokken (tijdens debat)', 'document_id': '33885-28'},
            {'result': 'Ingetrokken', 'document_id': '33885-14'},
            {'result': 'Verworpen', 'document_id': '33885-15'},
            {'result': 'Verworpen', 'document_id': '33885-16'},
            {'result': 'Verworpen', 'document_id': '33885-10'},
            {'result': 'Verworpen', 'document_id': '33885-13'},
            {'result': 'Aangenomen', 'document_id': '33885'}
        ]

        results = []
        for url in voting_page_urls:
            results += scraper.votings.get_votings_for_page(url)

        self.assertEqual(len(results), len(expected_results))
        for i in range(len(results)):
            # print('=============================')
            # print(results[i])
            # results[i].print_votes()
            self.assertEqual(results[i].get_result(), expected_results[i]['result'])
            self.assertEqual(results[i].get_document_id(), expected_results[i]['document_id'])

    def test_get_individual_votes(self):
        voting_page_urls = scraper.votings.get_voting_pages_for_dossier(self.dossier_nr_individual_votes)
        results = []
        for url in voting_page_urls:
            results += scraper.votings.get_votings_for_page(url)



