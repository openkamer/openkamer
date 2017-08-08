import datetime
import json
import os
import re

from django.test import TestCase

from wikidata import wikidata

import scraper.besluitenlijst
import scraper.documents
import scraper.dossiers
import scraper.government
import scraper.parliament_members
import scraper.persons
import scraper.political_parties
import scraper.votings


class TestDossierScraper(TestCase):
    dossier_id = '33711'

    def test_scrape_dossier_url(self):
        dossier_url = scraper.dossiers.search_dossier_url(self.dossier_id)
        self.assertEqual(dossier_url, 'https://www.tweedekamer.nl/kamerstukken/wetsvoorstellen/detail?id=2013Z16228&dossier=33711')

    def test_get_dossier_decision(self):
        dossier_url = scraper.dossiers.search_dossier_url(self.dossier_id)
        decision = scraper.dossiers.get_dossier_decision(dossier_url)
        self.assertEqual(decision, 'Wetsvoorstel zonder stemming aangenomen.')


class TestPoliticalPartyScraper(TestCase):

    def test_scrape_parties(self):
        parties = scraper.political_parties.search_parties()
        self.assertTrue(len(parties) > 10)
        for party in parties:
            self.assertTrue(party['name'])
            self.assertTrue(party['name_short'])

    def test_create_party_csv(self):
        filepath = './data/tmp/parties.csv'
        try:
            parties = scraper.political_parties.search_parties()
            scraper.political_parties.create_parties_csv(parties, filepath)
        finally:
            os.remove(filepath)


class TestParliamentMemberScraper(TestCase):

    def test_scrape_parliament_members(self):
        members = scraper.parliament_members.search_members()
        filepath = './data/tmp/members.csv'
        try:
            scraper.parliament_members.create_members_csv(members, filepath)
        finally:
            os.remove(filepath)


# class TestParliamentMembersParlementComScraper(TestCase):
#
#     def test_scrape(self):
#         members_json = scraper.parliament_members.search_members_check_json()
#         # with open('./data/secret/parliament_members_check.json', 'w') as fileout:
#         #     fileout.write(str(members_json))
#         members = json.loads(members_json)
#         for member in members:
#             self.assertNotEqual(member['name'], '')
#             self.assertNotEqual(member['initials'], '')
#             self.assertNotEqual(member['date_ranges'], [])


class TestKamervraagScraper(TestCase):
    kamervraag_url = 'https://zoek.officielebekendmakingen.nl/kv-tk-2017Z06952'

    def test_get_kamervraag_id_and_content(self):
        kamervraag_html_url = self.kamervraag_url + '.html'
        document_id, content_html, title = scraper.documents.get_kamervraag_document_id_and_content(kamervraag_html_url)
        self.assertEqual(document_id, 'kv-tk-2017Z06952')
        self.assertEqual(len(content_html), 5990)
        self.assertEqual(title, 'Vragen van het lid Bosman (VVD) aan de Minister van Binnenlandse Zaken en Koninkrijksrelaties over het bericht «Ziekenhuis Curaçao bezorgt NL strop» (ingezonden 26 mei 2017).')
        overheidnl_document_ids = scraper.documents.get_related_document_ids(self.kamervraag_url)
        self.assertEqual(len(overheidnl_document_ids), 1)
        self.assertEqual(overheidnl_document_ids[0], 'ah-tk-20162017-2167')

    def test_get_related_ids(self):
        url = 'https://zoek.officielebekendmakingen.nl/kv-tk-2017Z07318'
        related_document_ids = scraper.documents.get_related_document_ids(url)
        self.assertEqual(len(related_document_ids), 2)
        self.assertEqual(related_document_ids[0], 'ah-tk-20162017-2129')
        self.assertEqual(related_document_ids[1], 'ah-tk-20162017-2338')


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
        item = wikidata.WikidataItem(person_wikidata_id)
        parlement_id = item.get_parlement_and_politiek_id()
        self.assertEqual(parlement_id, expected_id)


class TestWetsvoorstellenDossierScraper(TestCase):
    max_results = 40

    def test_get_initiatief_wetsvoorstellen_dossier_ids(self):
        dossier_ids = scraper.dossiers.get_dossier_ids_wetsvoorstellen_initiatief(max_results=self.max_results)
        self.assertEqual(len(dossier_ids), self.max_results)
        dossier_ids = scraper.dossiers.get_dossier_ids_wetsvoorstellen_initiatief(max_results=self.max_results, filter_active=True)
        self.assertEqual(len(dossier_ids), self.max_results)

    def test_get_regering_wetsvoorstellen_dossier_ids(self):
        dossier_ids = scraper.dossiers.get_dossier_ids_wetsvoorstellen_regering(max_results=self.max_results)
        self.assertEqual(len(dossier_ids), self.max_results)
        dossier_ids = scraper.dossiers.get_dossier_ids_wetsvoorstellen_regering(max_results=self.max_results, filter_inactive=True)
        self.assertEqual(len(dossier_ids), self.max_results)

    def test_get_number_of_dossiers(self):
        number_initiatief, number_regering = scraper.dossiers.get_number_of_wetsvoorstellen()
        self.assertTrue(number_initiatief > 175)
        self.assertTrue(number_regering > 1389)


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
            self.assertEqual(results[i].get_document_id_without_rijkswet(), expected_results[i]['document_id'])

    def test_get_individual_votes(self):
        voting_page_urls = scraper.votings.get_voting_pages_for_dossier(self.dossier_nr_individual_votes)
        results = []
        for url in voting_page_urls:
            results += scraper.votings.get_votings_for_page(url)

    def test_get_votings_no_party_link(self):
        url = 'https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2014P16390'
        voting_results = scraper.votings.get_votings_for_page(url)
        self.assertEqual(len(voting_results), 1)
        voting_result = voting_results[0]
        self.assertEqual(len(voting_result.votes), 14)

    def test_get_votings_rijkswet(self):
        url ='https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2016P11874'
        voting_results = scraper.votings.get_votings_for_page(url)
        self.assertEqual(len(voting_results), 1)
        self.assertEqual(voting_results[0].get_result(), 'Aangenomen')
        self.assertEqual(voting_results[0].get_document_id(), '34158-(R2048)')
        self.assertEqual(voting_results[0].get_document_id_without_rijkswet(), '34158')
        self.assertEqual(voting_results[0].is_dossier_voting(), True)

    def test_get_voting_not_voted(self):
        url = 'https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2016P16759'
        voting_results = scraper.votings.get_votings_for_page(url)
        for result in voting_results:
            for vote in result.votes:
                if vote.party_name == 'Van Vliet':
                    self.assertEqual(vote.decision, scraper.votings.Vote.NOVOTE)

    def test_get_individual_vote_not_voted_and_mistake(self):
        url = 'https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2016P10653'
        voting_results = scraper.votings.get_votings_for_page(url)
        self.assertEqual(len(voting_results), 2)
        self.assertTrue(voting_results[0].is_individual())
        self.assertFalse(voting_results[1].is_individual())
        n_mistakes = 0
        n_novote = 0
        n_for = 0
        n_against = 0
        for vote in voting_results[0].votes:
            if vote.is_mistake:
                n_mistakes += 1
            if vote.decision == scraper.votings.Vote.NOVOTE:
                n_novote += 1
            elif vote.decision == scraper.votings.Vote.FOR:
                n_for += 1
            elif vote.decision == scraper.votings.Vote.AGAINST:
                n_against += 1
            else:
                self.assertTrue(False)
        self.assertEqual(len(voting_results[0].votes), 150)
        self.assertEqual(n_novote, 12)
        self.assertEqual(n_mistakes, 1)
        self.assertEqual(n_for, 68)
        self.assertEqual(n_against, 70)
        self.assertEqual(n_novote + n_for + n_against, 150)

    def test_get_voting_withdrawn(self):
        url = 'https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2016P16766'
        voting_results = scraper.votings.get_votings_for_page(url)
        self.assertEqual(len(voting_results), 1)
        voting = voting_results[0]
        self.assertEqual(voting.get_result(), 'Eerder ingetrokken (tijdens debat)')

    def test_voting_no_document_id(self):
        url = 'https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2010P04136'
        voting_results = scraper.votings.get_votings_for_page(url)
        for voting in voting_results:
            voting.get_document_id_without_rijkswet()


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
