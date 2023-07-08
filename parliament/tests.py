import datetime

from django.test import TestCase

from person.models import Person

from parliament.models import Parliament
from parliament.models import ParliamentMember
from parliament.models import PoliticalParty

from wikidata import wikidata


class TestPoliticalParty(TestCase):

    def test_get_political_party_memberships_wikidata(self):
        mark_rutte_wikidata_id = 'Q57792'
        item = wikidata.WikidataItem(mark_rutte_wikidata_id)
        parties = item.get_political_party_memberships()
        self.assertEqual(len(parties), 1)

    def test_get_political_party_memberships_ignore_local_and_youth_parties(self):
        loes_ypma_wikidata_id = 'Q1194971'
        item = wikidata.WikidataItem(loes_ypma_wikidata_id)
        parties = item.get_political_party_memberships()
        local_parties = 0
        youth_parties = 0
        for party in parties:
            if wikidata.WikidataItem(party['party_wikidata_id']).is_local_party:
                local_parties += 1
            if wikidata.WikidataItem(party['party_wikidata_id']).is_youth_party:
                youth_parties += 1
        self.assertEqual(3, len(parties))
        self.assertEqual(1, youth_parties)
        self.assertEqual(1, local_parties)

    def test_create_political_party(self):
        name = 'Houwers'
        name_short = 'Houwers'
        party = PoliticalParty.objects.create(name=name, name_short=name_short)
        party.update_info(language='nl')

    def test_find_party(self):
        name = 'Socialistische Partij'
        name_short = 'SP'
        party_expected = PoliticalParty.objects.create(name=name, name_short=name_short)
        party = PoliticalParty.find_party(name)
        self.assertEqual(party, party_expected)
        party = PoliticalParty.find_party(name_short)
        self.assertEqual(party, party_expected)
        party = PoliticalParty.find_party('sp')
        self.assertEqual(party, party_expected)
        party = PoliticalParty.find_party('SocialIstische parTij')
        self.assertEqual(party, party_expected)
        name = 'Group K/Ö'
        name_short = 'GrKO'
        party_expected = PoliticalParty.objects.create(name=name, name_short=name_short)
        party = PoliticalParty.find_party('GrKÖ')
        self.assertEqual(party, party_expected)
        party = PoliticalParty.find_party('GrKO')
        self.assertEqual(party, party_expected)

    def test_find_party_dash(self):
        party_expected = PoliticalParty.objects.create(name='Vrijzinnig Democratische Bond', name_short='VDB')
        party = PoliticalParty.find_party('Vrijzinnig Democratische Bond')
        self.assertEqual(party, party_expected)
        party = PoliticalParty.find_party('Vrijzinnig-Democratische Bond')
        self.assertEqual(party, party_expected)


class TestParliamentMembers(TestCase):
    fixtures = ['person.json', 'parliament.json']

    def test_get_members_at_date(self):
        tweede_kamer = Parliament.get_or_create_tweede_kamer()
        active_members = tweede_kamer.get_members_at_date(datetime.date(year=2016, month=6, day=1))
        self.assertEqual(len(active_members), 150)
        # print(len(active_members))  # TODO: check for number if members have non null joined/left fields

    def test_get_member_for_person_at_date(self):
        person = Person.find_by_fullname('Diederik Samsom')
        members_all = ParliamentMember.objects.filter(person=person)
        self.assertEqual(members_all.count(), 4)
        members = ParliamentMember.find_at_date(person, datetime.date(year=2016, month=6, day=1))
        self.assertEqual(members[0].joined, datetime.date(year=2012, month=9, day=20))
        self.assertEqual(members.count(), 1)
        self.assertEqual(members[0].person, person)
        members = ParliamentMember.find_at_date(person, datetime.date(year=2004, month=6, day=1))
        self.assertEqual(members[0].joined, datetime.date(year=2003, month=1, day=30))
        self.assertEqual(members.count(), 1)
        self.assertEqual(members[0].person, person)

    def test_find_members(self):
        person = Person.find_by_fullname('Diederik Samsom')
        member = ParliamentMember.find('Samsom', initials='D.M.')
        self.assertEqual(member.person, person)
        member = ParliamentMember.find('Samsom', initials='D.M.', date=datetime.date(year=2004, month=6, day=1))
        self.assertEqual(member.person, person)
        self.assertEqual(member.joined, datetime.date(year=2003, month=1, day=30))
        member = ParliamentMember.find('Samsom', initials='D.M.', date=datetime.date(year=2016, month=6, day=1))
        self.assertEqual(member.person, person)
        self.assertEqual(member.joined, datetime.date(year=2012, month=9, day=20))
