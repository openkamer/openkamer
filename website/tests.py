from django.test import TestCase
from django.test import Client

from scraper import political_parties
from scraper import parliament_members

from parliament.models import ParliamentMember

from document.models import Dossier
from document.models import Document
from document.models import Voting

from website.create import create_or_update_dossier


class TestCreateParliament(TestCase):

    def test_create_parliament(self):
        political_parties.create_parties()
        parliament_members.create_members()


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

    def test_dossiers_overview(self):
        response = self.client.get('/dossiers/')
        self.assertEqual(response.status_code, 200)

    def test_dossier_views(self):
        dossiers = Dossier.objects.all()
        for dossier in dossiers:
            response = self.client.get('/dossier/' + str(dossier.id) + '/')
            self.assertEqual(response.status_code, 200)

    def test_dossier_add(self):
        response = self.client.get('/dossier/add/34537/', follow=True)
        self.assertEqual(response.status_code, 200)

    def test_document_view(self):
        documents = Document.objects.all()
        for document in documents:
            response = self.client.get('/document/' + str(document.id) + '/')
            self.assertEqual(response.status_code, 200)

    def test_votings_overview(self):
        response = self.client.get('/votings/')
        self.assertEqual(response.status_code, 200)

    def test_voting_view(self):
        votings = Voting.objects.all()
        for voting in votings:
            response = self.client.get('/document/voting/' + str(voting.id) + '/')
            self.assertEqual(response.status_code, 200)

    def test_parties_overview(self):
        response = self.client.get('/parties/')
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
