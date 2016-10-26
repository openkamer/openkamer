from django.test import TestCase
from django.test import Client
from django.urls import reverse

from scraper import political_parties
from scraper import parliament_members

from person.models import Person

from government.models import Government

from parliament.models import ParliamentMember
from parliament.models import PartyMember
from parliament.models import PoliticalParty

from document.models import Agenda
from document.models import Dossier
from document.models import Document
from document.models import Voting

from website.create import create_or_update_dossier
from website.create import find_original_kamerstuk_id
from website.create import create_government


class TestCreateParliament(TestCase):

    def test_create_parliament(self):
        political_parties.create_parties()
        parliament_members.create_members()


class TestCreateGovernment(TestCase):
    fixtures = ['parliament_2016.json']

    @classmethod
    def setUpTestData(cls):
        rutte_2_wikidata_id = 'Q1638648'
        government = create_government(rutte_2_wikidata_id, max_members=4)

    def test_government_data(self):
        government = Government.objects.all()[0]
        self.assertEqual(government.name, 'Kabinet-Rutte II')
        members = government.members()
        persons = []
        for member in members:
            persons.append(member.person)
        party_members = PartyMember.objects.filter(person__in=persons)
        self.assertTrue(len(party_members) >= len(persons))

    def test_governements_view(self):
        response = self.client.get('/governments/')
        self.assertEqual(response.status_code, 200)

    def test_governement_view(self):
        governments = Government.objects.all()
        for government in governments:
            response = self.client.get('/government/' + str(government.id) + '/')
            self.assertEqual(response.status_code, 200)

    def test_api_governement(self):
        response = self.client.get('/api/government/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/api/ministry/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/api/governmentmember/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/api/governmentposition/')
        self.assertEqual(response.status_code, 200)


class TestFindParliamentMembers(TestCase):
    fixtures = ['parliament_2016.json']

    def test_find_member(self):
        surname = 'Zijlstra'
        forename = 'Halbe'
        initials = 'H.'
        member = ParliamentMember.find(surname=surname, initials=initials)
        self.assertEqual(member.person.forename, forename)

    def test_find_member_surname_prefix(self):
        surname = 'Weyenberg van'
        forename = 'Steven'
        initials = 'S.P.R.A.'
        member = ParliamentMember.find(surname=surname, initials=initials)
        self.assertEqual(member.person.forename, forename)
        surname = 'van Weyenberg'
        member = ParliamentMember.find(surname=surname, initials=initials)
        self.assertEqual(member.person.forename, forename)

    def test_find_member_non_ascii(self):
        surname = 'Koser Kaya'
        forename = 'Fatma'
        initials = 'F.'
        member = ParliamentMember.find(surname=surname, initials=initials)
        self.assertEqual(member.person.forename, forename)
        surname = 'Koşer Kaya'
        member = ParliamentMember.find(surname=surname, initials=initials)
        self.assertEqual(member.person.forename, forename)


class TestFindOriginalKamerstukId(TestCase):
    dossier_id = 33885

    def test_find_original_motie(self):
        expected_result = '33885-18'
        title = 'Gewijzigde motie van het lid Segers c.s. (t.v.v. 33885, nr.18) over de bevoegdheden van de Koninklijke Marechaussee'
        original_id = find_original_kamerstuk_id(self.dossier_id, title)
        self.assertEqual(original_id, expected_result)

    def test_find_original_amendement(self):
        title = 'Gewijzigd amendement van het lid Oskam ter vervanging van nr. 9 waarmee een verbod op illegaal pooierschap in het wetboek van strafrecht wordt geintroduceerd'
        expected_result = '33885-9'
        original_id = find_original_kamerstuk_id(self.dossier_id, title)
        self.assertEqual(original_id, expected_result)

    def test_find_original_voorstel_van_wet(self):
        title = 'Wijziging van de Wet regulering prostitutie en bestrijding misstanden seksbranche; Gewijzigd voorstel van wet '
        expected_result = '33885.voorstel_van_wet'
        original_id = find_original_kamerstuk_id(self.dossier_id, title)
        self.assertEqual(original_id, expected_result)

    def test_find_original_none(self):
        title = 'Motie van de leden Volp en Kooiman over monitoring van het nulbeleid'
        expected_result = ''
        original_id = find_original_kamerstuk_id(self.dossier_id, title)
        self.assertEqual(original_id, expected_result)


class TestWebsite(TestCase):
    fixtures = ['parliament_2016.json']

    @classmethod
    def setUpTestData(cls):
        create_or_update_dossier(33885)
        create_or_update_dossier(33506)
        cls.client = Client()

    def test_homepage(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_persons_overview(self):
        response = self.client.get('/persons/')
        self.assertEqual(response.status_code, 200)

    def test_person_overview(self):
        persons = Person.objects.all()[:10]
        for person in persons:
            response = self.client.get('/person/' + str(person.id) + '/')
            self.assertEqual(response.status_code, 200)

    def test_dossiers_overview(self):
        response = self.client.get(reverse('dossiers'))
        self.assertEqual(response.status_code, 200)

    def test_dossier_views(self):
        dossiers = Dossier.objects.all()
        for dossier in dossiers:
            response = self.client.get(reverse('dossier-tiles', args=(dossier.dossier_id,)))
            self.assertEqual(response.status_code, 200)

    def test_timeline_views(self):
        dossiers = Dossier.objects.all()
        for dossier in dossiers:
            response = self.client.get(reverse('dossier-timeline', args=(dossier.dossier_id,)))
            self.assertEqual(response.status_code, 200)

    def test_timeline_horizontal_views(self):
        dossiers = Dossier.objects.all()
        for dossier in dossiers:
            response = self.client.get(reverse('dossier-timeline-horizontal', args=(dossier.dossier_id,)))
            self.assertEqual(response.status_code, 200)

    def test_document_view(self):
        documents = Document.objects.all()
        for document in documents:
            response = self.client.get(reverse('document', args=(document.document_id,)))
            self.assertEqual(response.status_code, 200)

    def test_agenda_view(self):
        agendas = Agenda.objects.all()
        for agenda in agendas:
            response = self.client.get('/agenda/' + str(agenda.id) + '/')
            self.assertEqual(response.status_code, 200)

    def test_votings_overview(self):
        response = self.client.get(reverse('votings'))
        self.assertEqual(response.status_code, 200)

    def test_voting_view(self):
        votings = Voting.objects.all()
        for voting in votings:
            response = self.client.get('/document/voting/' + str(voting.id) + '/')
            self.assertEqual(response.status_code, 200)

    def test_parties_overview(self):
        response = self.client.get('/parties/')
        self.assertEqual(response.status_code, 200)

    def test_party_view(self):
        parties = PoliticalParty.objects.all()
        for party in parties:
            response = self.client.get(reverse('party', args=(party.name_short,)))
            self.assertEqual(response.status_code, 200)

    def test_parliament_members_overview(self):
        response = self.client.get('/parliamentmembers/')
        self.assertEqual(response.status_code, 200)

    def test_plot_example_view(self):
        response = self.client.get('/stats/exampleplots/')
        self.assertEqual(response.status_code, 200)

    def test_api_homepage(self):
        response = self.client.get('/api/')
        self.assertEqual(response.status_code, 200)

    def test_api_person(self):
        response = self.client.get('/api/person/')
        self.assertEqual(response.status_code, 200)

    def test_api_parliament(self):
        response = self.client.get('/api/parliament/')
        self.assertEqual(response.status_code, 200)

    def test_api_parliament_member(self):
        response = self.client.get('/api/parliamentmember/')
        self.assertEqual(response.status_code, 200)

    def test_api_party(self):
        response = self.client.get('/api/party/')
        self.assertEqual(response.status_code, 200)

    def test_api_party_member(self):
        response = self.client.get('/api/partymember/')
        self.assertEqual(response.status_code, 200)

    def test_api_document(self):
        response = self.client.get('/api/document/')
        self.assertEqual(response.status_code, 200)

    def test_api_kamerstuk(self):
        response = self.client.get('/api/kamerstuk/')
        self.assertEqual(response.status_code, 200)

    def test_api_submitter(self):
        response = self.client.get('/api/submitter/')
        self.assertEqual(response.status_code, 200)

    def test_api_dossier(self):
        response = self.client.get('/api/dossier/')
        self.assertEqual(response.status_code, 200)

    def test_api_voting(self):
        response = self.client.get('/api/voting/')
        self.assertEqual(response.status_code, 200)

    def test_api_voteparty(self):
        response = self.client.get('/api/voteparty/')
        self.assertEqual(response.status_code, 200)

    def test_api_voteindividual(self):
        response = self.client.get('/api/voteindividual/')
        self.assertEqual(response.status_code, 200)
