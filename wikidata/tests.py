from unittest import TestCase
from datetime import date

from wikidata import wikidata


class TestSearchParliamentMembers(TestCase):

    def test_search_all_ids(self):
        member_ids = wikidata.search_parliament_member_ids()
        self.assertTrue(len(member_ids) > 2200)


class TestGetParliamentMemberInfo(TestCase):

    def test_get_frans_timmermans(self):
        wikidata_id = 'Q32681'  # Frans Timmermans
        fullname = wikidata.get_label(wikidata_id)
        self.assertEqual(fullname, 'Frans Timmermans')
        given_name = wikidata.get_given_name(wikidata_id)
        self.assertEqual(given_name, 'Frans')
        birth_date = wikidata.get_birth_date(wikidata_id)
        self.assertEqual(birth_date, date(day=6, month=5, year=1961))
        parlement_positions = wikidata.get_parliament_positions_held(wikidata_id)
        self.assertEqual(len(parlement_positions), 2)


class TestPositionHeld(TestCase):
    wikidata_id_ft = 'Q32681'  # Frans Timmermans
    wikidata_id_wa = 'Q474763'  # Willem Aantjes
    wikidata_id_mr = 'Q57792'  # Mark Rutte

    def test_search_all(self):
        positions = wikidata.get_positions_held(self.wikidata_id_ft)
        self.assertEqual(len(positions), 4)
        positions = wikidata.get_positions_held(self.wikidata_id_wa)
        self.assertEqual(len(positions), 1)

    def test_search_parliament_member(self):
        positions = wikidata.get_parliament_positions_held(self.wikidata_id_ft)
        self.assertEqual(len(positions), 2)
        for position in positions:
            self.assertEqual(position['label'], 'member of the House of Representatives of the Netherlands')
        positions = wikidata.get_parliament_positions_held(self.wikidata_id_mr)
        self.assertEqual(len(positions), 3)
