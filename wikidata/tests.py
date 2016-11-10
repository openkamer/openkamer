import logging
from unittest import TestCase
import datetime

from wikidata import wikidata

logger = logging.getLogger(__name__)


class TestSearchParliamentMembers(TestCase):

    def test_search_all_ids(self):
        member_ids = wikidata.search_parliament_member_ids()
        self.assertTrue(len(member_ids) > 2200)


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


class TestPositionHeld(TestCase):
    wikidata_id_ft = 'Q32681'  # Frans Timmermans
    wikidata_id_wa = 'Q474763'  # Willem Aantjes
    wikidata_id_mr = 'Q57792'  # Mark Rutte

    def test_search_all(self):
        item = wikidata.WikidataItem(self.wikidata_id_ft)
        positions = item.get_positions_held()
        self.assertEqual(len(positions), 4)
        item = wikidata.WikidataItem(self.wikidata_id_wa)
        positions = item.get_positions_held()
        self.assertEqual(len(positions), 1)

    def test_search_parliament_member(self):
        item = wikidata.WikidataItem(self.wikidata_id_ft)
        positions = item.get_parliament_positions_held()
        self.assertEqual(len(positions), 2)
        for position in positions:
            self.assertEqual(position['id'], 'Q18887908')
        item = wikidata.WikidataItem(self.wikidata_id_mr)
        positions = item.get_parliament_positions_held()
        self.assertEqual(len(positions), 3)
