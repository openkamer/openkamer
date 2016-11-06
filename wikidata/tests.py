from unittest import TestCase

from wikidata import wikidata


class TestSearchParliamentMembers(TestCase):

    def test_search_all(self):
        wikidata.search_parliament_members()


class TestPositionHeld(TestCase):
    wikidata_id = 'Q32681'  # Frans Timmermans

    def test_search_all(self):
        positions = wikidata.get_positions_held(self.wikidata_id)
        self.assertEqual(len(positions), 8)

    def test_search_parliament_member(self):
        positions = wikidata.get_positions_held(self.wikidata_id, filter_position_id='Q18887908')
        self.assertEqual(len(positions), 6)
