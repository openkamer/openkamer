import logging
from unittest import TestCase
import datetime

from wikidata import wikidata
from wikidata import government as wikidata_government

logger = logging.getLogger(__name__)


class TestSearchParliamentMembers(TestCase):

    def test_search_ids_all(self):
        member_ids = wikidata.search_parliament_member_ids()
        self.assertEqual(len(member_ids), len(set(member_ids)))
        self.assertTrue(len(member_ids) > 2200)

    def test_search_ids_with_start_date(self):
        member_ids = wikidata.search_parliament_member_ids_with_start_date()
        self.assertEqual(len(member_ids), len(set(member_ids)))
        self.assertTrue(len(member_ids) > 530)


class TestGetParliamentMemberInfo(TestCase):

    def test_get_frans_timmermans(self):
        logger.info('BEGIN')
        wikidata_id = 'Q32681'  # Frans Timmermans
        item = wikidata.WikidataItem(wikidata_id)
        fullname = item.get_label()
        self.assertEqual(fullname, 'Frans Timmermans')
        given_name = item.get_given_names()[0]
        self.assertEqual(given_name, 'Frans')
        birth_date = item.get_birth_date()
        self.assertEqual(birth_date, datetime.date(day=6, month=5, year=1961))
        parlement_positions = item.get_parliament_positions_held()
        self.assertEqual(len(parlement_positions), 2)
        logger.info('END')

    def test_get_fraction(self):
        wikidata_id = 'Q2801440'  # Martin van Rooijen, 50Plus
        item_50plus_id = 'Q27122891'
        item = wikidata.WikidataItem(wikidata_id)
        positions = item.get_positions_held()
        fraction_id = None
        for position in positions:
            if position['id'] == wikidata.PARLIAMENT_MEMBER_DUTCH_ITEM_ID:
                fraction_id = position['part_of_id']
        self.assertEqual(fraction_id, item_50plus_id)


class TestPositionHeld(TestCase):
    wikidata_id_ft = 'Q32681'  # Frans Timmermans
    wikidata_id_wa = 'Q474763'  # Willem Aantjes
    wikidata_id_mr = 'Q57792'  # Mark Rutte

    def test_search_all(self):
        item = wikidata.WikidataItem(self.wikidata_id_ft)
        positions = item.get_positions_held()
        self.assertEqual(len(positions), 6)
        item = wikidata.WikidataItem(self.wikidata_id_wa)
        positions = item.get_positions_held()
        self.assertEqual(len(positions), 1)

    def test_search_parliament_member(self):
        item = wikidata.WikidataItem(self.wikidata_id_ft)
        positions = item.get_parliament_positions_held()
        self.assertEqual(len(positions), 2)
        for position in positions:
            self.assertEqual(position['id'], wikidata.PARLIAMENT_MEMBER_DUTCH_ITEM_ID)
        item = wikidata.WikidataItem(self.wikidata_id_mr)
        positions = item.get_parliament_positions_held()
        self.assertEqual(len(positions), 4)


class TestFindPoliticalParty(TestCase):

    def test_search_pvdd(self):
        wikidata_id = wikidata.search_political_party_id('PvdD', language='nl')
        item = wikidata.WikidataItem(wikidata_id)
        label = item.get_label(language='nl')
        self.assertEqual(label, 'Partij voor de Dieren')

    def test_search_groenlinks(self):
        wikidata_id = wikidata.search_political_party_id('GL', language='nl')
        self.assertIsNotNone(wikidata_id)
        self.assertGreaterEqual(wikidata_id, 'Q667680')
        item = wikidata.WikidataItem(wikidata_id)
        label = item.get_label(language='nl')
        self.assertEqual(label, 'GroenLinks')

    def test_search_vvd(self):
        wikidata_id = wikidata.search_political_party_id('VgetVD', language='nl')
        item = wikidata.WikidataItem(wikidata_id)
        label = item.get_label(language='nl')
        self.assertEqual(label, 'Volkspartij voor Vrijheid en Democratie')

    def test_is_political_party(self):
        wikidata_id = 'Q275441'  # PvdA
        item = wikidata.WikidataItem(wikidata_id)
        is_pp = item.is_political_party()
        self.assertTrue(is_pp)

    def test_is_fractie(self):
        wikidata_id = 'Q28044800'  # Lid-Monasch
        item = wikidata.WikidataItem(wikidata_id)
        is_fractie = item.is_fractie()
        self.assertTrue(is_fractie)

    def test_search_group_houwers(self):
        wikidata_id = wikidata.search_political_party_id('Houwers', language='nl')
        self.assertEqual(wikidata_id, 'Q28044763')
        item = wikidata.WikidataItem(wikidata_id)
        label = item.get_label(language='nl')
        self.assertEqual(label, 'Lid-Houwers')

    def test_search_socialist_party(self):
        wikidata_id = wikidata.search_political_party_id('Socialistische Partij', language='nl')
        self.assertEqual(wikidata_id, 'Q849580')
        item = wikidata.WikidataItem(wikidata_id)
        label = item.get_label(language='nl')
        self.assertEqual(label, 'Socialistische Partij')


class TestDate(TestCase):

    def test_date(self):
        date_str = '+2016-12-25T00:00:00Z'
        date = wikidata.WikidataItem.get_date(date_str)
        self.assertEqual(date.day, 25)
        self.assertEqual(date.month, 12)
        self.assertEqual(date.year, 2016)
        date_str = '+2016-00-00T00:00:00Z'
        date = wikidata.WikidataItem.get_date(date_str)
        self.assertEqual(date.day, 1)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.year, 2016)


class TestPersonProperties(TestCase):

    def test_get_twitter_username(self):
        wikidata_id = 'Q560780'
        item = wikidata.WikidataItem(wikidata_id)
        self.assertEqual(item.get_twitter_username(), 'diederiksamsom')


class TestGovernmentScraper(TestCase):
    rutte_2_wikidata_id = 'Q1638648'

    def test(self):
        government = wikidata_government.get_government(self.rutte_2_wikidata_id)
        self.assertEqual(government['name'], 'Kabinet-Rutte II')
        self.assertEqual(government['start_date'], datetime.date(2012, 11, 5))

    def test_get_members(self):
        members = wikidata_government.get_government_members(self.rutte_2_wikidata_id)
        self.assertGreater(len(members), 10)

    def test_get_parlement_and_politiek_id(self):
        person_wikidata_id = 'Q32681'
        expected_id = 'vg09llk9rzrp'
        item = wikidata.WikidataItem(person_wikidata_id)
        parlement_id = item.get_parlement_and_politiek_id()
        self.assertEqual(parlement_id, expected_id)
