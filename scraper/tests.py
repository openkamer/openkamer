import json
import datetime
import re

from django.test import TestCase

from wikidata import wikidata

import scraper.documents
import scraper.votings
import scraper.government
import scraper.persons

# metadata = scraper.documents.get_metadata(document_id='kst-33885-7')
# print(metadata)

# page_url = 'https://zoek.officielebekendmakingen.nl/kst-33885-7.html?zoekcriteria=%3fzkt%3dEenvoudig%26pst%3d%26vrt%3d33885%26zkd%3dInDeGeheleText%26dpr%3dAfgelopenDag%26spd%3d20160522%26epd%3d20160523%26sdt%3dDatumBrief%26ap%3d%26pnr%3d1%26rpp%3d10%26_page%3d4%26sorttype%3d1%26sortorder%3d4&resultIndex=34&sorttype=1&sortorder=4'
# scraper.documents.get_document_id(page_url)

# scraper.documents.search_politieknl_dossier(33885)


class TestBesluitenlijstScraper(TestCase):

    def test_regex(self):
        test_str = "FIN          Overig     20.   Agendapunt: Brief ombudsman Rotterdam inzake griffierecht in huisvuilzaken     Zaak:  Brief regering"
        pattern = "\d+\.\s+Agendapunt"
        # result = re.split(pattern=pattern, string=test_str)
        result = re.sub(pattern=pattern, repl=TestBesluitenlijstScraper.add_new_line, string=test_str)
        print(result)

    def format_whitespaces(self, text):
        pattern = "\s{4,}"
        result = re.sub(
            pattern=pattern,
            repl='\n\n',
            string=text
        )
        return result

    def format_agendapunten(self, text):
        pattern = "\d+\.\s+Agendapunt:"
        result = re.sub(
            pattern=pattern,
            repl=TestBesluitenlijstScraper.add_double_new_line,
            string=text
        )
        return result

    def remove_page_numbers(self, text):
        pattern = r'\n\s+\d+\s+\n'
        result = re.sub(
            pattern=pattern,
            repl='\n\n',
            string=text
        )
        return result

    def test_test(self):
        text = scraper.documents.besluitenlijst_pdf_to_text()
        text = self.format_whitespaces(text)
        text = self.format_agendapunten(text)
        text = self.add_line_before('Zaak:', text)
        text = self.add_line_before('Besluit:', text)
        text = self.add_line_before('Noot:', text)
        text = self.add_line_before('Volgcommissie\(s\):', text)
        text = self.add_line_before('Griffier:', text)
        text = self.add_line_before('Activiteitnummer:', text)
        text = self.remove_page_numbers(text)
        with open('data/lijst.txt', 'w') as fileout:
            fileout.write(text)
        print(text)

    @staticmethod
    def add_line_before(pattern, text):
        result = re.sub(
            pattern=pattern,
            repl=TestBesluitenlijstScraper.add_new_line,
            string=text
        )
        return result

    @staticmethod
    def add_new_line(matchobj):
        return '\n' + matchobj.group(0)

    @staticmethod
    def add_double_new_line(matchobj):
        return '\n\n' + matchobj.group(0)


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
        print(government)
        self.assertEqual(government['name'], 'Kabinet-Rutte II')
        self.assertEqual(government['start_date'], datetime.date(2012, 11, 5))

    def test_get_members(self):
        members = scraper.government.get_government_members(self.rutte_2_wikidata_id)
        for member in members:
            print(member)

    def test_get_parlement_and_politiek_id(self):
        person_wikidata_id = 'Q32681'
        expected_id = 'vg09llk9rzrp'
        parlement_id = wikidata.get_parlement_and_politiek_id(person_wikidata_id)
        self.assertEqual(parlement_id, expected_id)


class TestWetsvoorstellenDossierScraper(TestCase):
    max_results = 40

    def test_get_initiatief_wetsvoorstellen_dossier_ids(self):
        dossier_ids = scraper.documents.get_dossier_ids_wetsvoorstellen_initiatief(max_results=self.max_results)
        print('initiatief wetsvoorstel dossiers found: ' + str(len(dossier_ids)))
        # with open('data/dossier_ids_wetsvoorstellen_initiatief.txt', 'w') as fileout:
        #     for dossier_id in dossier_ids:
        #         fileout.write(dossier_id + '\n')
        self.assertEqual(len(dossier_ids), self.max_results)

    def test_get_regering_wetsvoorstellen_dossier_ids(self):
        dossier_ids = scraper.documents.get_dossier_ids_wetsvoorstellen_regering(max_results=self.max_results)
        print('regering wetsvoorstel dossiers found: ' + str(len(dossier_ids)))
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



